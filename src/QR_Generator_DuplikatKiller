
# hier ist der Code um zu verhindern das QR Code Duplikate entstehen.
# Dieser muss noch in den späteren BücherApp Projekt eingefügt werden. 

# 10.02.26 //  Denis ; Luis 


import qrcode

def generate_qr_for_book(db_conn, book_id: int):
    # 1. Prüfen, ob schon ein QR-Code existiert
    if qr_exists_for_book(db_conn, book_id):
        print("Fehler: Für diese Buch_ID existiert bereits ein QR-Code!")
        return

    # 2. QR-Inhalt bauen (hier Beispiel-URL, kann auch nur die ID sein)
    qr_data = f"https://deine-app/books/{book_id}"

    # 3. QR-Code erzeugen
    features = qrcode.QRCode(version=1, box_size=40, border=3)
    features.add_data(qr_data)
    features.make(fit=True)
    img = features.make_image(fill_color='black', back_color='white')

    # 4. Datei speichern (Name z.B. abhängig von book_id)
    filename = f"BooktrackQR_Code_{book_id}.png"
    img.save(filename)

    # 5. Datensatz in der DB speichern
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO qr_codes (book_id, qr_data, file_path) VALUES (?, ?, ?)",
        (book_id, qr_data, filename)
    )
    db_conn.commit()
