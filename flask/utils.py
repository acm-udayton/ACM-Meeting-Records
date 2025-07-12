import hashlib
import qrcode

def sha_hash(string_to_hash):
    """ Wrapper function for hashlib's SHA-512 hash. """
    m = hashlib.sha3_512()
    m.update(bytes(string_to_hash, "utf-8"))
    return m.hexdigest()

def make_qr(base_url, event_id, rand_code):
    """ Create a QR code from the arguments provided. """
    # Data to encode
    target = f"{base_url}/?id={event_id}&code={rand_code}"

    # Create QR code object
    qr = qrcode.QRCode(version=1, 
                       error_correction=qrcode.constants.ERROR_CORRECT_L, 
                       box_size=10, 
                       border=4)

    # Add data to the QR code
    qr.add_data(target)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image
    qr_file = f"qrcode_{event_id}.png"
    img.save(qr_file)
    return qr_file
