"""Seed and UI languages (independent of geographic territory)."""

from __future__ import annotations

import os

from customer360.territory.models import ForeclosureAssetLabels, InteractionCopy

LANGUAGE_IDS = ("en", "fr", "es", "he", "ar")

LANGUAGE_LABELS: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "he": "Hebrew",
    "ar": "Arabic",
}

UI_LANGUAGE_IDS = LANGUAGE_IDS


def language_catalog() -> list[dict[str, str]]:
    return [{"code": code, "label": LANGUAGE_LABELS[code]} for code in LANGUAGE_IDS]


def get_language(language_id: str) -> str:
    key = (language_id or "").strip().lower()
    if key not in LANGUAGE_LABELS:
        known = ", ".join(LANGUAGE_IDS)
        raise ValueError(f"Unknown language {language_id!r}; expected one of: {known}")
    return key


def resolve_seed_language(
    *,
    seed_language: str | None = None,
    territory_id: str | None = None,
    env: os._Environ[str] | None = None,
) -> str:
    if seed_language and str(seed_language).strip():
        return get_language(str(seed_language))
    environ = env if env is not None else os.environ
    raw = environ.get("CUSTOMER360_SEED_LANGUAGE")
    if raw and str(raw).strip():
        return get_language(str(raw))
    return "en"


def _copy_en() -> InteractionCopy:
    return InteractionCopy(
        product_searches=(
            "Compare pension balanced vs equity tracks",
            "Critical illness rider eligibility",
            "Add family member to health supplementary",
            "Study fund contribution limits",
            "Life insurance coverage calculator",
            "Property policy renewal quote",
        ),
        help_searches=(
            "How to update payment method",
            "Cancel or surrender a policy",
            "Missing premium payment options",
            "Portal login verification code",
            "Download annual policy statement",
            "Complaint escalation process",
            "Change communication preferences",
        ),
        agent_topics=(
            ("Premium increase explanation", "billing", True),
            ("Switch investment track on pension", "investments", True),
            ("Request policy cancellation", "retention", False),
            ("Coverage gap after job change", "coverage", True),
            ("Foreclosure impact on policies", "legal", False),
            ("Claim status follow-up", "claims", True),
            ("Duplicate charge on credit card", "billing", False),
        ),
        review_titles=(
            "Mobile app experience",
            "Claims handling speed",
            "Agent courtesy on phone",
            "Pension statement clarity",
            "Health plan network",
            "Digital self-service tools",
        ),
        review_detail_positive="Praised quick resolution.",
        review_detail_negative="Requested clearer follow-up.",
        agent_detail_resolved="Agent provided next steps.",
        agent_detail_unresolved="Customer awaiting callback.",
        web_session_detail="Session recorded in digital analytics.",
    )


def _copy_he() -> InteractionCopy:
    return InteractionCopy(
        product_searches=(
            "השוואת מסלולי פנסיה מאוזנים מול מנייתיים",
            "זכאות לכיסוי מחלות קשות",
            "הוספת בן משפחה לביטוח בריאות משלים",
            "תקרות הפקדה לקרן השתלמות",
            "מחשבון כיסוי ביטוח חיים",
            "הצעת מחיר לחידוש ביטוח דירה",
        ),
        help_searches=(
            "איך לעדכן אמצעי תשלום",
            "ביטול או פדיון פוליסה",
            "אפשרויות לתשלום חוב פרמיה",
            "קוד אימות לכניסה לפורטל",
            "הורדת אישור פוליסה שנתי",
            "תהליך הגשת תלונה",
            "שינוי העדפות תקשורת",
        ),
        agent_topics=(
            ("הסבר על עליית פרמיה", "billing", True),
            ("מעבר מסלול השקעה בפנסיה", "investments", True),
            ("בקשה לביטול פוליסה", "retention", False),
            ("פער כיסוי אחרי החלפת מקום עבודה", "coverage", True),
            ("השפעת עיקול על פוליסות", "legal", False),
            ("מעקב סטטוס תביעה", "claims", True),
            ("חיוב כפול בכרטיס אשראי", "billing", False),
        ),
        review_titles=(
            "חוויית אפליקציה סלולרית",
            "מהירות טיפול בתביעות",
            "אדיבות נציג בטלפון",
            "בהירות דוח פנסיה",
            "רשת מסלולי בריאות",
            "כלי שירות עצמי דיגיטליים",
        ),
        review_detail_positive="שיבח/ה פתרון מהיר.",
        review_detail_negative="ביקש/ה מעקב ברור יותר.",
        agent_detail_resolved="הנציג/ה נתן/נה צעדים להמשך.",
        agent_detail_unresolved="הלקוח/ה ממתין/ה לשיחה חוזרת.",
        web_session_detail="הסשן נרשם באנליטיקה דיגיטלית.",
    )


def _copy_es() -> InteractionCopy:
    return InteractionCopy(
        product_searches=(
            "Comparar fondos de pensiones equilibrados vs renta variable",
            "Elegibilidad para cobertura de enfermedad crítica",
            "Añadir familiar al seguro de salud complementario",
            "Límites de aportación al plan de estudios",
            "Calculadora de cobertura de vida",
            "Cotización de renovación de seguro de hogar",
        ),
        help_searches=(
            "Cómo actualizar el método de pago",
            "Cancelar o rescindir una póliza",
            "Opciones por recibo impagado",
            "Código de verificación del portal",
            "Descargar certificado anual de la póliza",
            "Proceso de reclamación",
            "Cambiar preferencias de comunicación",
        ),
        agent_topics=(
            ("Explicación del aumento de prima", "billing", True),
            ("Cambiar tramo de inversión del plan de pensiones", "investments", True),
            ("Solicitar cancelación de póliza", "retention", False),
            ("Brecha de cobertura tras cambio de empleo", "coverage", True),
            ("Impacto de embargo en pólizas", "legal", False),
            ("Seguimiento del estado del siniestro", "claims", True),
            ("Cargo duplicado en tarjeta", "billing", False),
        ),
        review_titles=(
            "Experiencia en la app móvil",
            "Rapidez en la gestión de siniestros",
            "Trato del agente telefónico",
            "Claridad del extracto de pensiones",
            "Red del plan de salud",
            "Herramientas digitales de autoservicio",
        ),
        review_detail_positive="Destacó la rapidez en la resolución.",
        review_detail_negative="Pidió un seguimiento más claro.",
        agent_detail_resolved="El agente indicó los siguientes pasos.",
        agent_detail_unresolved="Cliente pendiente de devolución de llamada.",
        web_session_detail="Sesión registrada en analítica digital.",
    )


def _copy_fr() -> InteractionCopy:
    return InteractionCopy(
        product_searches=(
            "Comparer les fonds de retraite équilibrés et actions",
            "Éligibilité à la couverture maladies graves",
            "Ajouter un membre de la famille à la complémentaire santé",
            "Plafonds de versement sur le plan épargne formation",
            "Calculateur de couverture décès",
            "Devis de renouvellement assurance habitation",
        ),
        help_searches=(
            "Comment mettre à jour le moyen de paiement",
            "Résilier ou racheter un contrat",
            "Options en cas de prime impayée",
            "Code de vérification du portail",
            "Télécharger l'attestation annuelle",
            "Procédure de réclamation",
            "Modifier les préférences de communication",
        ),
        agent_topics=(
            ("Explication de la hausse de prime", "billing", True),
            ("Changer la ligne d'investissement retraite", "investments", True),
            ("Demande de résiliation", "retention", False),
            ("Lacune de couverture après changement d'emploi", "coverage", True),
            ("Impact d'une saisie sur les contrats", "legal", False),
            ("Suivi du statut de sinistre", "claims", True),
            ("Double débit sur carte bancaire", "billing", False),
        ),
        review_titles=(
            "Expérience application mobile",
            "Rapidité de traitement des sinistres",
            "Courtoisie du conseiller téléphonique",
            "Clarté du relevé retraite",
            "Réseau de soins",
            "Outils de self-service digital",
        ),
        review_detail_positive="A salué la rapidité de résolution.",
        review_detail_negative="A demandé un suivi plus clair.",
        agent_detail_resolved="Le conseiller a indiqué les prochaines étapes.",
        agent_detail_unresolved="Client en attente de rappel.",
        web_session_detail="Session enregistrée dans l'analytique digitale.",
    )


def _copy_ar() -> InteractionCopy:
    return InteractionCopy(
        product_searches=(
            "مقارنة مسارات التقاعد المتوازنة مقابل الأسهم",
            "أهلية تغطية الأمراض الحرجة",
            "إضافة فرد للتأمين الصحي التكميلي",
            "حدود مساهمة صندوق الادخار",
            "حاسبة تغطية التأمين على الحياة",
            "عرض تجديد تأمين الممتلكات",
        ),
        help_searches=(
            "كيفية تحديث طريقة الدفع",
            "إلغاء أو استرداد الوثيقة",
            "خيارات الدفع المتأخر",
            "رمز التحقق من البوابة",
            "تنزيل كشف الوثيقة السنوي",
            "إجراءات تقديم الشكاوى",
            "تغيير تفضيلات التواصل",
        ),
        agent_topics=(
            ("شرح زيادة القسط", "billing", True),
            ("تغيير مسار الاستثمار للتقاعد", "investments", True),
            ("طلب إلغاء الوثيقة", "retention", False),
            ("فجوة التغطية بعد تغيير الوظيفة", "coverage", True),
            ("أثر الحجز على الوثائق", "legal", False),
            ("متابعة حالة المطالبة", "claims", True),
            ("رسوم مكررة على البطاقة", "billing", False),
        ),
        review_titles=(
            "تجربة تطبيق الجوال",
            "سرعة معالجة المطالبات",
            "أسلوب الوكيل الهاتفي",
            "وضوح كشف التقاعد",
            "شبكة الخطة الصحية",
            "أدوات الخدمة الذاتية الرقمية",
        ),
        review_detail_positive="أشاد بالحل السريع.",
        review_detail_negative="طلب متابعة أوضح.",
        agent_detail_resolved="قدم الوكيل الخطوات التالية.",
        agent_detail_unresolved="العميل بانتظار اتصال.",
        web_session_detail="تم تسجيل الجلسة في التحليلات الرقمية.",
    )


_INTERACTION: dict[str, InteractionCopy] = {
    "en": _copy_en(),
    "fr": _copy_fr(),
    "es": _copy_es(),
    "he": _copy_he(),
    "ar": _copy_ar(),
}

_FORECLOSURE: dict[str, ForeclosureAssetLabels] = {
    "en": ForeclosureAssetLabels(yes="Yes", no="No", policy="Policy", claim="Claim"),
    "fr": ForeclosureAssetLabels(yes="Oui", no="Non", policy="Contrat", claim="Sinistre"),
    "es": ForeclosureAssetLabels(yes="Sí", no="No", policy="Póliza", claim="Siniestro"),
    "he": ForeclosureAssetLabels(yes="כן", no="לא", policy="פוליסה", claim="תביעה"),
    "ar": ForeclosureAssetLabels(yes="نعم", no="لا", policy="وثيقة", claim="مطالبة"),
}


def get_interaction_copy(language_id: str) -> InteractionCopy:
    return _INTERACTION[get_language(language_id)]


def get_foreclosure_labels(language_id: str) -> ForeclosureAssetLabels:
    return _FORECLOSURE[get_language(language_id)]
