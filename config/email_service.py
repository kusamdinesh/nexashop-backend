import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Environment, FileSystemLoader
from config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Setup Jinja2 template engine
template_env = Environment(
    loader=FileSystemLoader(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/emails')
    )
)

def render_template(template_name: str, **kwargs) -> str:
    template = template_env.get_template(template_name)
    return template.render(**kwargs)

def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str
) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not set — email not sent")
        return False

    try:
        message = Mail(
            from_email=(settings.FROM_EMAIL, settings.FROM_NAME),
            to_emails=(to_email, to_name),
            subject=subject,
            html_content=html_content
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email} — status {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

# ── Email Functions ──────────────────────────────────

def send_order_confirmation(
    customer_email: str,
    customer_name: str,
    order_number: str,
    items: list,
    subtotal: float,
    tax: float,
    total: float,
    notes: Optional[str] = None
) -> bool:
    html = render_template(
        "order_confirmation.html",
        customer_name=customer_name,
        order_number=order_number,
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        notes=notes
    )
    return send_email(
        to_email=customer_email,
        to_name=customer_name,
        subject=f"Order Confirmed — {order_number} 🛒",
        html_content=html
    )

def send_order_status_update(
    customer_email: str,
    customer_name: str,
    order_number: str,
    new_status: str
) -> bool:
    status_map = {
        "processing": {
            "icon": "⚙️",
            "label": "Being Processed",
            "description": "Your order is being prepared."
        },
        "shipped": {
            "icon": "🚚",
            "label": "Shipped",
            "description": "Your order is on its way! Expected delivery in 3-5 business days."
        },
        "delivered": {
            "icon": "✅",
            "label": "Delivered",
            "description": "Your order has been delivered. Enjoy!"
        },
        "cancelled": {
            "icon": "❌",
            "label": "Cancelled",
            "description": "Your order has been cancelled. Contact us if you have questions."
        }
    }

    status_info = status_map.get(new_status, {
        "icon": "📦",
        "label": new_status.title(),
        "description": f"Your order status is now {new_status}."
    })

    html = render_template(
        "order_status_update.html",
        customer_name=customer_name,
        order_number=order_number,
        status_icon=status_info["icon"],
        status_label=status_info["label"],
        status_description=status_info["description"]
    )

    return send_email(
        to_email=customer_email,
        to_name=customer_name,
        subject=f"Order Update — {order_number} {status_info['icon']}",
        html_content=html
    )

def send_low_stock_alert(products: list) -> bool:
    if not products:
        return False

    html = render_template(
        "low_stock_alert.html",
        products=products
    )

    return send_email(
        to_email=settings.ADMIN_EMAIL,
        to_name="NexaShop Admin",
        subject=f"⚠️ Low Stock Alert — {len(products)} product(s) need attention",
        html_content=html
    )

def send_welcome_email(
    user_email: str,
    full_name: str
) -> bool:
    html = render_template(
        "welcome.html",
        full_name=full_name
    )

    return send_email(
        to_email=user_email,
        to_name=full_name,
        subject="Welcome to NexaShop! 🛒",
        html_content=html
    )