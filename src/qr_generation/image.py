import qrcode


def generate_qr_image(payload: str):
    """
    Erzeugt ein QR-Bildobjekt im Speicher (keine Dateispeicherung).
    """
    qr = qrcode.QRCode(version=1, box_size=40, border=3)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    return image
