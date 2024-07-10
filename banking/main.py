#main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from mongoengine import connect, Document, StringField, FloatField, ValidationError, NotUniqueError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB
try:
    connect(db="banking", host="mongodb://localhost:27017/account_credentials")
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Account(Document):
    account_number = StringField(required=True, unique=True)
    name = StringField(required=True)
    phone = StringField(required=True)
    balance = FloatField(default=0.0)

def generate_account_number():
    import random
    return str(random.randint(1000000000, 9999999999))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/create_account", response_class=HTMLResponse)
async def create_account(request: Request, name: str = Form(...), phone: str = Form(...)):
    try:
        account_number = generate_account_number()
        account = Account(account_number=account_number, name=name, phone=phone)
        account.save()
        logger.info(f"Created account with account number: {account_number}")
        return templates.TemplateResponse("account.html", {"request": request, "account": account})
    except NotUniqueError:
        logger.error("Account number already exists.")
        return HTMLResponse("Account number already exists. Please try again.", status_code=400)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return HTMLResponse(f"Validation error: {e}", status_code=400)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return HTMLResponse(f"An error occurred: {e}", status_code=500)

@app.post("/deposit", response_class=HTMLResponse)
async def deposit(request: Request, account_number: str = Form(...), amount: float = Form(...)):
    try:
        account = Account.objects(account_number=account_number).first()
        if account:
            account.balance += amount
            account.save()
            logger.info(f"Deposited {amount} to account {account_number}")
        return templates.TemplateResponse("account.html", {"request": request, "account": account})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return HTMLResponse(f"An error occurred: {e}", status_code=500)

@app.post("/withdraw", response_class=HTMLResponse)
async def withdraw(request: Request, account_number: str = Form(...), amount: float = Form(...)):
    try:
        account = Account.objects(account_number=account_number).first()
        if account:
            if account.balance >= amount:
                account.balance -= amount
                account.save()
                logger.info(f"Withdrew {amount} from account {account_number}")
                return templates.TemplateResponse("account.html", {"request": request, "account": account})
            else:
                error_message = "Insufficient balance."
                logger.error(error_message)
                return templates.TemplateResponse("account.html", {"request": request, "account": account, "error": error_message})
        else:
            error_message = "Account not found."
            logger.error(error_message)
            return HTMLResponse(error_message, status_code=404)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return HTMLResponse(f"An error occurred: {e}", status_code=500)

@app.post("/balance", response_class=HTMLResponse)
async def balance(request: Request, account_number: str = Form(...)):
    try:
        account = Account.objects(account_number=account_number).first()
        return templates.TemplateResponse("account.html", {"request": request, "account": account})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return HTMLResponse(f"An error occurred: {e}", status_code=500)