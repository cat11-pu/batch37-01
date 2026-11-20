class PiiRedactor:
    def __init__(self):
        self.masks = {"email": "[email]", "phone": "[phone]", "id": "[id]", "ip": "[ip]"}

    def redact(self, value):
        return value
