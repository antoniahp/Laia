from domain.entities import Business
from domain.exceptions import BusinessNotFound, InvalidReview, MessageNotSent, SessionExpired


class ReviewBusinessCommand:
    """Una administradora verifica o rechaza un negocio, o guarda las teclas de su menú."""

    def __init__(self, repositories, message_service):
        self.repositories = repositories
        self.message_service = message_service

    def execute(self, dto):
        admin = self.repositories.accounts.find(dto.admin_id)
        if not admin:
            raise SessionExpired()
        admin.require_admin()
        business = self.repositories.businesses.find(dto.business_id)
        if not business:
            raise BusinessNotFound()

        previous = business.status
        if dto.status:
            if dto.status == Business.VERIFIED:
                business.verify("admin")
            elif dto.status == Business.REJECTED:
                business.reject()
            elif dto.status == Business.PENDING:
                business.status = Business.PENDING
            else:
                raise InvalidReview()
        if dto.ivr_digits is not None:
            business.set_ivr_digits(dto.ivr_digits)
        if dto.language:
            Business.check_data(business.name, dto.language)
            business.language = dto.language
        self.repositories.businesses.save(business)

        if business.status != previous:
            self._tell_proposer(business)
        return business

    def _tell_proposer(self, business):
        proposer = business.created_by
        if not proposer or not proposer.has_telegram:
            return
        text = "ya está verificado: Laia puede llamar" if business.is_verified else "no se ha aprobado"
        try:
            self.message_service.send(proposer.telegram_chat_id, f"{business.name} {text}.")
        except MessageNotSent:
            pass
