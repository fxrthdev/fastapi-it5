"""Data models and database operations for Users and Expenses."""

from pydantic import BaseModel, Field


# --- User Models ---
class UserInput(BaseModel):
    name: str = Field(min_length=1)
    monthly_budget: float = Field(ge=0)

    @staticmethod
    def create_user(user_input, database_connection):
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, monthly_budget) VALUES (?, ?)",
                (user_input.name, user_input.monthly_budget),
            )
            return connection.execute(
                "SELECT id, name, monthly_budget FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

    @staticmethod
    def get_user_summary(user_id, database_connection):
        """Transactional process: Calculate total spending vs remaining budget."""
        with database_connection() as connection:
            user = connection.execute(
                "SELECT id, name, monthly_budget FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            if not user:
                return None

            total_spent = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?",
                (user_id,),
            ).fetchone()["total"]

            remaining = user["monthly_budget"] - total_spent
            is_over_budget = remaining < 0

            return {
                "user_id": user["id"],
                "name": user["name"],
                "monthly_budget": user["monthly_budget"],
                "total_spent": total_spent,
                "remaining_budget": remaining,
                "is_over_budget": is_over_budget,
            }


class User(UserInput):
    id: int


# --- Expense Models ---
class ExpenseInput(BaseModel):
    title: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str = Field(default="General", min_length=1)
    user_id: int = Field(gt=0)

    @staticmethod
    def list_expenses_by_user(user_id, database_connection):
        with database_connection() as connection:
            return connection.execute(
                """
                SELECT e.id, e.title, e.amount, e.category, e.user_id, u.name AS user_name
                FROM expenses e
                JOIN users u ON e.user_id = u.id
                WHERE e.user_id = ?
                ORDER BY e.id
                """,
                (user_id,),
            ).fetchall()

    @staticmethod
    def record_expense_transaction(expense_input, database_connection):
        """Transactional process: Validates user existence and logs expense."""
        with database_connection() as connection:
            # Check foreign key target existence
            user = connection.execute(
                "SELECT id FROM users WHERE id = ?", (expense_input.user_id,)
            ).fetchone()

            if not user:
                return None  # Triggers 404 in endpoint

            cursor = connection.execute(
                "INSERT INTO expenses (title, amount, category, user_id) VALUES (?, ?, ?, ?)",
                (
                    expense_input.title,
                    expense_input.amount,
                    expense_input.category,
                    expense_input.user_id,
                ),
            )
            return connection.execute(
                "SELECT id, title, amount, category, user_id FROM expenses WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

    @staticmethod
    def delete_expense(expense_id, database_connection):
        with database_connection() as connection:
            connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


class Expense(ExpenseInput):
    id: int