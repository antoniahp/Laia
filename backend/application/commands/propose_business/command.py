from django.conf import settings

from domain.entities import Business
from domain.exceptions import BusinessRejected, MessageNotSent, SessionExpired
from domain.rules.languages import language_name
from domain.rules.phone_format import parse_callable_phone


class ProposeBusinessCommand:
    """Alguien propone un negocio. Si Google lo confirma, queda verificado; si no, lo revisa una administradora."""

    def __init__(self, repositories, verification_service, message_service):
        self.repositories = repositories
        self.verification_service = verification_service
        self.message_service = message_service

    def execute(self, dto):
        proposer = self.repositories.accounts.find(dto.account_id)
        if not proposer:
            raise SessionExpired()
        Business.check_data(dto.name, dto.language)
        phone = parse_callable_phone(dto.phone, settings.LAIA["ALLOWED_COUNTRIES"])

        existing = self.repositories.businesses.find_by_phone(phone.e164)
        if existing:
            if existing.status == Business.REJECTED:
                raise BusinessRejected()
            return existing

        business = Business(name=dto.name.strip(), phone=phone.e164, country=phone.country, language=dto.language, created_by=proposer)
        if proposer.is_admin:
            business.verify("admin")  # la administradora se fía de sí misma
        elif self.verification_service.find(business.name, phone.e164, dto.city):
            business.verify("google_places")
        self.repositories.businesses.save(business)

        if not business.is_verified:
            self._ask_admins(business, proposer)
        return business

    def _ask_admins(self, business, proposer):
        text = (
            f"🏪 Nuevo negocio para revisar\n{business.name}\n{business.phone} ({business.country}, "
            f"{language_name(business.language)})\nPropuesto por {proposer.email}"
        )
        buttons = [[("✅ Verificar", f"b|{business.id}|ok"), ("❌ Rechazar", f"b|{business.id}|no")]]
        for admin in self.repositories.accounts.list_admins_with_telegram():
            try:
                self.message_service.send(admin.telegram_chat_id, text, buttons)
            except MessageNotSent:
                pass
