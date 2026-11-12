import base64
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


class Command(BaseCommand):
    help = "Generate VAPID key files used for Web Push notifications"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Replace existing VAPID key files")

    def handle(self, *args, **options):
        private_path = Path(settings.VAPID_PRIVATE_KEY_FILE)
        public_path = Path(settings.BASE_DIR) / "vapid_public.txt"
        if (private_path.exists() or public_path.exists()) and not options["force"]:
            raise CommandError("VAPID key file(s) already exist. Use --force only if you intend to rotate them.")
        private_path.parent.mkdir(parents=True, exist_ok=True)
        key = ec.generate_private_key(ec.SECP256R1())
        private_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        public_text = base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode("ascii")
        private_path.write_bytes(private_pem)
        try:
            os.chmod(private_path, 0o600)
        except OSError:
            pass
        public_path.write_text(public_text, encoding="ascii")
        self.stdout.write(self.style.SUCCESS("VAPID keys generated."))
        self.stdout.write(f"Private key: {private_path} (keep secret; never upload/share)")
        self.stdout.write(f"Public key: {public_path}")
        self.stdout.write("Restart Django workers so settings reloads VAPID_PUBLIC_KEY.")
