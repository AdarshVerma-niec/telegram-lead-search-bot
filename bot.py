import os
import pandas as pd

from dotenv import load_dotenv

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


# ============================================================
# 1. LOAD ENVIRONMENT
# ============================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ============================================================
# 2. LOAD EXCEL FILE
# ============================================================

EXCEL_PATH = r"C:\Users\HP\OneDrive\Desktop\telegram_bot\data\486M+ Apollo.io Database Sample Leads.xlsx"

df = pd.read_excel(EXCEL_PATH)

print(f"Loaded {len(df)} leads")

print("\nColumns:")
print(df.columns.tolist())


# ============================================================
# 3. SEARCH STATES
# ============================================================

FIRST_NAME, LAST_NAME, COMPANY, JOB_TITLE = range(4)


# ============================================================
# 4. START COMMAND
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "I can search the lead database.\n\n"
        "Use /search to find a person.\n\n"
        "First name is required.\n"
        "Last name, company and job title are optional."
    )


# ============================================================
# 5. START SEARCH
# ============================================================

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["search"] = {}

    await update.message.reply_text(
        "🔎 Enter the first name:\n\n"
        "First name is required."
    )

    return FIRST_NAME


# ============================================================
# 6. GET FIRST NAME
# ============================================================

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    first_name = update.message.text.strip()

    # First name cannot be skipped
    if first_name == "-":

        await update.message.reply_text(
            "❌ First name is required.\n\n"
            "Please enter a first name."
        )

        return FIRST_NAME

    context.user_data["search"]["first_name"] = first_name

    await update.message.reply_text(
        "Enter last name:\n\n"
        "Type - to skip."
    )

    return LAST_NAME


# ============================================================
# 7. GET LAST NAME
# ============================================================

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    last_name = update.message.text.strip()

    if last_name == "-":
        last_name = ""

    context.user_data["search"]["last_name"] = last_name

    await update.message.reply_text(
        "Enter company name:\n\n"
        "Type - to skip."
    )

    return COMPANY


# ============================================================
# 8. GET COMPANY
# ============================================================

async def get_company(update: Update, context: ContextTypes.DEFAULT_TYPE):

    company = update.message.text.strip()

    if company == "-":
        company = ""

    context.user_data["search"]["company"] = company

    await update.message.reply_text(
        "Enter job title:\n\n"
        "Type - to skip."
    )

    return JOB_TITLE


# ============================================================
# 9. GET JOB TITLE + SEARCH
# ============================================================

async def get_job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    job_title = update.message.text.strip()

    if job_title == "-":
        job_title = ""

    context.user_data["search"]["job_title"] = job_title

    # Get search information
    search = context.user_data["search"]

    await update.message.reply_text("🔍 Searching...")


    # ========================================================
    # NORMALIZE SEARCH INPUT
    # ========================================================

    first_name = search["first_name"].strip().lower()
    last_name = search["last_name"].strip().lower()
    company = search["company"].strip().lower()
    job_title = search["job_title"].strip().lower()


    # ========================================================
    # DEBUG
    # ========================================================

    print("\n========== SEARCH DEBUG ==========")

    print("First name:", repr(first_name))
    print("Last name:", repr(last_name))
    print("Company:", repr(company))
    print("Job title:", repr(job_title))


    # ========================================================
    # SEARCH DATABASE
    # ========================================================

    results = df.copy()


    # --------------------------------------------------------
    # FIRST NAME - REQUIRED
    # --------------------------------------------------------

    results = results[
        results["first_name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(first_name)
    ]

    print("After first name:", len(results))


    # --------------------------------------------------------
    # LAST NAME - OPTIONAL
    # --------------------------------------------------------

    if last_name:

        results = results[
            results["last_name"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                last_name,
                regex=False,
                na=False
            )
        ]

        print("After last name:", len(results))


    # --------------------------------------------------------
    # COMPANY - OPTIONAL
    # --------------------------------------------------------

    if company:

        results = results[
            results["organization_name"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                company,
                regex=False,
                na=False
            )
        ]

        print("After company:", len(results))


    # --------------------------------------------------------
    # JOB TITLE - OPTIONAL
    # --------------------------------------------------------

    if job_title:

        results = results[
            results["job_title"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                job_title,
                regex=False,
                na=False
            )
        ]

        print("After job title:", len(results))


    print("==================================\n")


    # ========================================================
    # NO RESULTS
    # ========================================================

    if results.empty:

        await update.message.reply_text(
            "❌ No matching person found."
        )

        context.user_data.clear()

        return ConversationHandler.END


    # ========================================================
    # SHOW MAXIMUM 5 RESULTS
    # ========================================================

    results = results.head(5)


    await update.message.reply_text(
        f"✅ Found {len(results)} result(s).\n"
        "Showing maximum 5."
    )


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    for _, row in results.iterrows():

        first_name_result = clean(row["first_name"])
        last_name_result = clean(row["last_name"])

        company_result = clean(row["organization_name"])
        email = clean(row["person_email"])
        phone = clean(row["person_phone"])
        linkedin = clean(row["person_linkedin_url"])

        location = clean(row["person_location_country"])
        city = clean(row["person_location_city"])


        message = (
            f"👤 {first_name_result} {last_name_result}\n\n"

            f"🏢 Company: {company_result}\n"
            f"📧 Email: {email}\n"
            f"📱 Phone: {phone}\n"
            f"🔗 LinkedIn: {linkedin}\n"
            f"📍 Location: {location}\n"
            f"🏙️ City: {city}"
        )


        await update.message.reply_text(message)


    context.user_data.clear()

    return ConversationHandler.END


# ============================================================
# 10. CLEAN DATA
# ============================================================

def clean(value):

    if pd.isna(value):
        return "Not available"

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return "Not available"

    return value


# ============================================================
# 11. CANCEL
# ============================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Search cancelled."
    )

    return ConversationHandler.END


# ============================================================
# 12. CREATE BOT
# ============================================================

app = Application.builder().token(TOKEN).build()


# Normal /start command
app.add_handler(
    CommandHandler("start", start)
)


# Search conversation
search_conversation = ConversationHandler(

    entry_points=[
        CommandHandler("search", search_start)
    ],

    states={

        FIRST_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_first_name
            )
        ],

        LAST_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_last_name
            )
        ],

        COMPANY: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_company
            )
        ],

        JOB_TITLE: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                get_job_title
            )
        ],

    },

    fallbacks=[
        CommandHandler("cancel", cancel)
    ],
)


app.add_handler(search_conversation)


# ============================================================
# 13. RUN BOT
# ============================================================

print("🤖 Bot is running...")

app.run_polling()