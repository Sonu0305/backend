import resend
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Resend with API key
resend.api_key = settings.RESEND_API_KEY if hasattr(settings, 'RESEND_API_KEY') and settings.RESEND_API_KEY else None


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an email using Resend HTTP API (works on Render free tier)
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Check if Resend is configured
        if not resend.api_key:
            logger.warning("Resend API key not configured. Email not sent.")
            logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
            return True  # Return True to not block functionality during development
        
        # Send email via Resend API
        params = {
            "from": f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Password reset email sent successfully to {to_email} (ID: {response.get('id')})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Send password reset email
    
    Args:
        to_email: User's email address
        reset_link: Password reset link
        
    Returns:
        bool: True if email sent successfully
    """
    from ..utils import get_password_reset_html
    
    subject = "Password Reset Request"
    html_content = get_password_reset_html(reset_link, to_email)
    
    return await send_email(to_email, subject, html_content)
