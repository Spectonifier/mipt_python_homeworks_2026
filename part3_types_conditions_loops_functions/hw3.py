from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_LENGTHS = [2, 2, 4]
FEBRUARY_NUMBER = 2
MONTHS_IN_YEAR = 12
CATEGORY_PARTS_COUNT = 2
INCOME_QUERY_LENGTH = 3
COST_CATEGORIES_QUERY_LENGTH = 2
COST_QUERY_LENGTH = 4
STATS_QUERY_LENGTH = 2

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
}


financial_transactions_storage: list[dict[str, Any]] = []


def save_failed_transaction() -> None:
    financial_transactions_storage.append({})


def is_leap_year(year: int) -> bool:
    if year % 4 == 0 and year % 100 != 0:
        return True
    return year % 400 == 0


def get_days_in_month(month: int, year: int) -> int:
    if month == FEBRUARY_NUMBER:
        return 28 + is_leap_year(year)
    if month in (4, 6, 9, 11):
        return 30
    return 31


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    date_list = maybe_dt.split("-")

    if len(date_list) != len(DATE_LENGTHS):
        return None

    for part, expected_length in zip(date_list, DATE_LENGTHS, strict=True):
        if len(part) != expected_length or not part.isdigit():
            return None

    day, month, year = map(int, date_list)

    if month < 1 or month > MONTHS_IN_YEAR:
        return None

    days_in_month = get_days_in_month(month, year)
    if day < 1 or day > days_in_month:
        return None

    return day, month, year


def extract_amount(maybe_amount: str) -> float | None:
    normalized_amount = maybe_amount.replace(",", ".")

    if normalized_amount.count(".") > 1:
        return None

    if normalized_amount.startswith(("+", "-")):
        sign = normalized_amount[0]
        normalized_amount = normalized_amount[1:]
    else:
        sign = ""

    if not normalized_amount:
        return None

    if "." in normalized_amount:
        left_part, right_part = normalized_amount.split(".", maxsplit=1)
        if not left_part or not right_part:
            return None
        if not left_part.isdigit() or not right_part.isdigit():
            return None
    elif not normalized_amount.isdigit():
        return None

    return float(f"{sign}{normalized_amount}")


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        save_failed_transaction()
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(income_date)
    if date is None:
        save_failed_transaction()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"amount": amount, "date": date})
    return OP_SUCCESS_MSG


def is_valid_category(category_name: str) -> bool:
    category_parts = category_name.split("::")
    if len(category_parts) != CATEGORY_PARTS_COUNT:
        return False

    common_category, target_category = category_parts
    return common_category in EXPENSE_CATEGORIES and target_category in EXPENSE_CATEGORIES[common_category]


def get_target_category(category_name: str) -> str:
    _, target_category = category_name.split("::", maxsplit=1)
    return target_category


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        save_failed_transaction()
        return NONPOSITIVE_VALUE_MSG

    if not is_valid_category(category_name):
        save_failed_transaction()
        return NOT_EXISTS_CATEGORY

    date = extract_date(income_date)
    if date is None:
        save_failed_transaction()
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(
        f"{common_category}::{target_category}"
        for common_category, subcategories in EXPENSE_CATEGORIES.items()
        for target_category in subcategories
    )


def is_same_month(lhs: tuple[int, int, int], rhs: tuple[int, int, int]) -> bool:
    return lhs[1] == rhs[1] and lhs[2] == rhs[2]


def date_comparator(lhs: tuple[int, int, int], rhs: tuple[int, int, int]) -> bool:
    for i in range(2, -1, -1):
        if lhs[i] != rhs[i]:
            return lhs[i] < rhs[i]
    return False


def format_amount(amount: float) -> str:
    formatted_amount = f"{amount:.2f}"
    if formatted_amount.endswith("00"):
        return formatted_amount[:-3]
    if formatted_amount.endswith("0"):
        return formatted_amount[:-1]
    return formatted_amount


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG

    total_capital = 0.0
    monthly_income = 0.0
    monthly_expenses = 0.0
    expenses_by_category: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if not transaction:
            continue

        transaction_date = transaction["date"]
        if date_comparator(date, transaction_date):
            continue

        amount = transaction["amount"]
        if "category" in transaction:
            total_capital -= amount
            if is_same_month(transaction_date, date):
                monthly_expenses += amount
                target_category = get_target_category(transaction["category"])
                expenses_by_category[target_category] = expenses_by_category.get(target_category, 0.0) + amount
        else:
            total_capital += amount
            if is_same_month(transaction_date, date):
                monthly_income += amount

    monthly_capital = monthly_income - monthly_expenses
    result_type = "profit"
    result_amount = monthly_capital

    if monthly_capital < 0:
        result_type = "loss"
        result_amount = -monthly_capital

    stats_lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {total_capital:.2f} rubles",
        f"This month, the {result_type} amounted to {result_amount:.2f} rubles.",
        f"Income: {monthly_income:.2f} rubles",
        f"Expenses: {monthly_expenses:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    sorted_categories = sorted(expenses_by_category.items(), key=lambda item: item[0].lower())
    for index, (category_name, amount) in enumerate(sorted_categories, start=1):
        stats_lines.append(f"{index}. {category_name}: {format_amount(amount)}")

    return "\n".join(stats_lines)


def print_handler_result(result: str) -> None:
    print(result)
    if result == NOT_EXISTS_CATEGORY:
        categories_info = cost_categories_handler()
        if categories_info:
            print(categories_info)


def process_income_query(input_parts: list[str]) -> None:
    if len(input_parts) != INCOME_QUERY_LENGTH:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = extract_amount(input_parts[1])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    print(income_handler(amount, input_parts[2]))


def process_cost_query(input_parts: list[str]) -> None:
    if len(input_parts) == COST_CATEGORIES_QUERY_LENGTH and input_parts[1] == "categories":
        print(cost_categories_handler())
        return

    if len(input_parts) != COST_QUERY_LENGTH:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = extract_amount(input_parts[2])
    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    print_handler_result(cost_handler(input_parts[1], amount, input_parts[3]))


def process_stats_query(input_parts: list[str]) -> None:
    if len(input_parts) != STATS_QUERY_LENGTH:
        print(UNKNOWN_COMMAND_MSG)
        return

    print(stats_handler(input_parts[1]))


def process_query() -> bool:
    input_line = input().strip()
    if not input_line:
        return False

    input_parts = input_line.split()
    command_name = input_parts[0]

    if command_name == "income":
        process_income_query(input_parts)
    elif command_name == "cost":
        process_cost_query(input_parts)
    elif command_name == "stats":
        process_stats_query(input_parts)
    else:
        print(UNKNOWN_COMMAND_MSG)

    return True


def main() -> None:
    while process_query():
        continue


if __name__ == "__main__":
    main()
