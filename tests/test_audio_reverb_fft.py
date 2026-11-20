import pytest

import audio_reverb_fft as ar


def reverb(impulse=(0.5, 0.5), block_size=2, wet=1.0, dry=0.0):
    return ar.BlockReverb(list(impulse), block_size, wet, dry)


def test_empty_impulse_is_rejected():
    with pytest.raises(ValueError):
        ar.BlockReverb([], 4, 0.5, 0.5)


def test_block_size_must_be_positive():
    with pytest.raises(ValueError):
        ar.BlockReverb([1.0], 0, 0.5, 0.5)


def test_wet_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        ar.BlockReverb([1.0], 4, 1.5, 0.5)


def test_dry_out_of_range_is_rejected():
    with pytest.raises(ValueError):
        ar.BlockReverb([1.0], 4, 0.5, -0.1)


def test_process_length_includes_tail():
    out = reverb((1.0, 0.5, 0.25), 2).process([1.0, 2.0])
    assert out == [1.0, 2.5, 1.25, 0.5]


def test_process_matches_direct_convolution():
    impulse = [0.5, 0.25, 0.125]
    samples = [2.0, 4.0, 6.0]
    expected = [0.0] * (len(samples) + len(impulse) - 1)
    for i, x in enumerate(samples):
        for j, h in enumerate(impulse):
            expected[i + j] += x * h
    assert reverb(impulse, 2).process(samples) == expected


def test_dry_signal_is_padded():
    out = reverb((1.0, 2.0, 3.0), 2, wet=0.0, dry=1.0).process([2.0, 4.0])
    assert out == [2.0, 4.0, 0.0, 0.0]


def test_wet_and_dry_are_mixed():
    out = reverb((2.0,), 1, wet=0.25, dry=0.75).process([4.0])
    assert out == [5.0]


def test_block_size_does_not_change_output():
    small = reverb((0.5, 1.0), 1, wet=1.0, dry=0.5).process([1.0, 2.0, 3.0, 4.0])
    large = reverb((0.5, 1.0), 3, wet=1.0, dry=0.5).process([1.0, 2.0, 3.0, 4.0])
    assert small == large == [1.0, 3.0, 5.0, 7.0, 4.0]


def test_push_returns_one_block_sized_output():
    unit = reverb((0.5, 0.5), 2)
    assert len(unit.push([1.0, 2.0, 3.0])) == 3


def test_streaming_matches_one_shot():
    one_shot = reverb((0.5, 0.5), 2).process([1.0, 2.0, 3.0, 4.0])
    unit = reverb((0.5, 0.5), 2)
    streamed = unit.push([1.0, 2.0]) + unit.push([3.0, 4.0]) + unit.flush()
    assert streamed == one_shot


def test_flush_returns_tail_length():
    unit = reverb((0.5, 1.0, 0.25), 2)
    unit.push([1.0, 2.0])
    assert len(unit.flush()) == 2


def test_flush_without_input_is_empty():
    assert reverb((0.5, 0.5), 2).flush() == []


def test_reset_clears_streaming_state():
    unit = reverb((0.5, 0.5), 2)
    unit.push([1.0, 2.0])
    unit.reset()
    assert unit.state()["input_samples"] == 0
    assert unit.flush() == []


def test_state_snapshot_is_independent():
    unit = reverb((0.5, 0.5), 2, wet=0.3, dry=0.7)
    snapshot = unit.state()
    snapshot["impulse"][0] = 9.0
    snapshot["wet"] = 9.0
    assert unit.state()["impulse"][0] == 0.5
    assert unit.state()["wet"] == 0.3
