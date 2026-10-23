import html

from jose import jwt

from app.core.config import settings


def _e(value) -> str:
    """HTML-escape any scraped value (None becomes an empty string)."""
    return html.escape("" if value is None else str(value), quote=True)


def _one_line(value) -> str:
    """Collapse whitespace/newlines so values are safe inside an email subject."""
    return " ".join(str(value or "").split())


def generate_unsubscribe_token(user_id) -> str:
    """Generates a signed, stateless token for single-click unsubscribe."""
    return jwt.encode(
        {"user_id": str(user_id), "action": "unsubscribe"},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def generate_match_email(user, matches: list) -> dict:
    """
    Generates HTML and plain text payloads for a list of internship matches.
    Handles both single instant matches and daily digests.
    """
    unsub_token = generate_unsubscribe_token(user.id)
    unsub_url = f"{settings.PUBLIC_API_URL}/subscriptions/unsubscribe?token={unsub_token}"

    is_digest = len(matches) > 1
    if is_digest:
        subject = f"Your Daily Internship Digest - {len(matches)} New Matches"
    else:
        subject = f"New Internship Match: {_one_line(matches[0].offer.title)}"

    # ---- Plain text ----
    text_lines = [f"Hello, we found {len(matches)} new internship(s) matching your criteria:\n"]
    for match in matches:
        offer = match.offer
        text_lines.append(f"- {offer.title} at {offer.company} ({offer.country or 'n/a'})")
        text_lines.append(f"  Match Score: {match.score}% | Type: {offer.internship_type or 'n/a'}")
        text_lines.append(f"  Apply here: {offer.canonical_url}\n")
    text_lines.append(f"\nUnsubscribe or manage your alerts here: {unsub_url}")
    text_content = "\n".join(text_lines)

    # ---- HTML ----
    html_lines = [
        "<html><body style='font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;'>",
        "<h2 style='color: #2563eb;'>InternshipRadar AI</h2>",
        f"<p>Hello, we found <strong>{len(matches)} new opportunity(s)</strong> matching your profile.</p>",
    ]

    for match in matches:
        offer = match.offer
        published = offer.published_at.strftime("%Y-%m-%d") if offer.published_at else "Recent"
        first_reason = match.reasons[0] if match.reasons else "General match"
        workplace = (offer.workplace_type or "n/a").capitalize()
        internship_type = (offer.internship_type or "n/a").upper()
        html_lines.append(
            "<div style='border: 1px solid #e5e7eb; padding: 15px; margin-bottom: 15px; border-radius: 8px;'>"
            f"<h3 style='margin-top: 0; margin-bottom: 5px; color: #1f2937;'>{_e(offer.title)}</h3>"
            f"<p style='margin: 0 0 10px 0; color: #4b5563;'><strong>{_e(offer.company)}</strong>"
            f" • {_e(offer.location_raw)} • {_e(workplace)}</p>"
            f"<p style='font-size: 14px;'><strong>Score:</strong> {match.score}% • "
            f"<strong>Type:</strong> {_e(internship_type)} • <strong>Published:</strong> {_e(published)}</p>"
            f"<p style='font-size: 13px; color: #6b7280; font-style: italic;'>Why it matched: {_e(first_reason)}</p>"
            f"<a href='{_e(offer.canonical_url)}' style='display: inline-block; background: #2563eb; "
            "color: #fff; padding: 8px 16px; text-decoration: none; border-radius: 4px; "
            "font-weight: bold;'>View Application</a>"
            "</div>"
        )

    html_lines.append(
        "<div style='margin-top: 30px; font-size: 12px; color: #9ca3af;'>"
        "<p>You are receiving this because you subscribed to InternshipRadar alerts.</p>"
        f"<p><a href='{_e(unsub_url)}' style='color: #9ca3af; text-decoration: underline;'>"
        "Unsubscribe or change your alert frequency</a></p>"
        "</div></body></html>"
    )

    return {
        "subject": subject,
        "text_content": text_content,
        "html_content": "".join(html_lines),
    }