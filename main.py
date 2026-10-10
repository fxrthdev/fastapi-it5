"""Create the FastAPI app and connect route modules."""

from fastapi import FastAPI, HTTPException

from app.database import database_connection, initialize_database
from app.models import ExpenseInput, UserInput

app = FastAPI(
    title="Personal Expense & Budget Information System",
    description="Manages users, budgets, and logs expense transactions with pure SQLite.",
)


@app.get("/")
def home():
    return {
        "system": "Expense Tracker & Budget Management System",
        "docs": "Visit /docs to test the API.",
    }


# --- User Endpoints ---

@app.post("/users", status_code=201)
def create_user(user: UserInput):
    result = UserInput.create_user(
        user_input=user, database_connection=database_connection
    )
    return {"user": dict(result)}


@app.get("/users/{user_id}/budget-summary")
def get_user_budget_summary(user_id: int):
    """Transactional Endpoint: Calculates budget usage and status."""
    summary = UserInput.get_user_summary(
        user_id=user_id, database_connection=database_connection
    )
    if not summary:
        raise HTTPException(status_code=404, detail="User not found")
    return {"summary": summary}


# --- Expense Endpoints ---

@app.post("/expenses", status_code=201)
def record_expense(expense: ExpenseInput):
    """Transactionally logs an expense associated with a user."""
    result = ExpenseInput.record_expense_transaction(
        expense_input=expense, database_connection=database_connection
    )
    if not result:
        raise HTTPException(
            status_code=404, detail="User ID does not exist. Cannot record expense."
        )
    return {"expense": dict(result)}


@app.get("/users/{user_id}/expenses")
def list_user_expenses(user_id: int):
    results = ExpenseInput.list_expenses_by_user(
        user_id=user_id, database_connection=database_connection
    )
    return {"expenses": [dict(r) for r in results]}


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    ExpenseInput.delete_expense(
        expense_id=expense_id, database_connection=database_connection
    )
    return {"message": "Expense deleted successfully"}


initialize_database()