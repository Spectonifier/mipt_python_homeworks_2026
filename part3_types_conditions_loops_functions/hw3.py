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

DAY_INDEX = 0
MONTH_INDEX = 1
YEAR_INDEX = 2
MAX_AMOUNT_PARTS = 2

CAPITAL_KEY = "capital"
INCOME_KEY = "income"
EXPENSES_KEY = "expenses"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory")
}

Date = tuple[int, int, int]
Transaction = dict[str, Any]

financial_transactions_storage: list[Transaction] = []


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


def _has_valid_date_parts(date_parts: list[str]) -> bool:
    if len(date_parts) != len(DATE_LENGTHS):
        return False
    for part, expected_length in zip(date_parts, DATE_LENGTHS, strict=True):
        if len(part) != expected_length or not part.isdigit():
            return False
    return True


def _build_date(date_parts: list[str]) -> Date:
    return (
        int(date_parts[DAY_INDEX]),
        int(date_parts[MONTH_INDEX]),
        int(date_parts[YEAR_INDEX]),
    )


def _is_valid_date(date: Date) -> bool:
    month = date[MONTH_INDEX]
    if month < 1 or month > MONTHS_IN_YEAR:
        return False
    day = date[DAY_INDEX]
    return 1 <= day <= get_days_in_month(month, date[YEAR_INDEX])


def extract_date(maybe_dt: str) -> Date | None:
    date_parts = maybe_dt.split("-")
    if not _has_valid_date_parts(date_parts):
        return None
    date = _build_date(date_parts)
    if not _is_valid_date(date):
        return None
    return date


def _strip_sign(amount: str) -> str:
    if amount.startswith(("+", "-")):
        return amount[1:]
    return amount


def _has_valid_amount_body(amount_body: str) -> bool:
    amount_parts = amount_body.split(".")
    return len(amount_parts) <= MAX_AMOUNT_PARTS and all(amount_parts) and all(
        part.isdigit() for part in amount_parts
    )


def extract_amount(maybe_amount: str) -> float | None:
    normalized_amount = maybe_amount.replace(",", ".")
    if not _has_valid_amount_body(_strip_sign(normalized_amount)):
        return None
    return float(normalized_amount)


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


def _month_and_year(date: Date) -> tuple[int, int]:
    return date[MONTH_INDEX], date[YEAR_INDEX]


def is_same_month(lhs: Date, rhs: Date) -> bool:
    return _month_and_year(lhs) == _month_and_year(rhs)


def date_comparator(lhs: Date, rhs: Date) -> bool:
    return lhs[::-1] < rhs[::-1]


def format_amount(amount: float) -> str:
    formatted_amount = f"{amount:.2f}"
    if formatted_amount.endswith("00"):
        return formatted_amount[:-3]
    if formatted_amount.endswith("0"):
        return formatted_amount[:-1]
    return formatted_amount


def _empty_totals() -> dict[str, float]:
    return {
        CAPITAL_KEY: 0,
        INCOME_KEY: 0,
        EXPENSES_KEY: 0,
    }


def _should_skip_transaction(transaction: Transaction, report_date: Date) -> bool:
    if not transaction:
        return True
    return date_comparator(report_date, transaction["date"])


def _update_category_total(category_totals: dict[str, float], category_name: str, amount: float) -> None:
    target_category = get_target_category(category_name)
    if target_category not in category_totals:
        category_totals[target_category] = 0
    category_totals[target_category] += amount


def _apply_income_transaction(transaction: Transaction, report_date: Date, totals: dict[str, float]) -> None:
    amount = transaction["amount"]
    totals[CAPITAL_KEY] += amount
    if is_same_month(transaction["date"], report_date):
        totals[INCOME_KEY] += amount


def _apply_expense_transaction(
    transaction: Transaction,
    report_date: Date,
    totals: dict[str, float],
    category_totals: dict[str, float],
) -> None:
    amount = transaction["amount"]
    totals[CAPITAL_KEY] -= amount
    if is_same_month(transaction["date"], report_date):
        totals[EXPENSES_KEY] += amount
        _update_category_total(category_totals, transaction["category"], amount)


def _calculate_stats(report_date: Date) -> tuple[dict[str, float], dict[str, float]]:
    totals = _empty_totals()
    category_totals: dict[str, float] = {}
    for transaction in financial_transactions_storage:
        if _should_skip_transaction(transaction, report_date):
            continue
        if "category" in transaction:
            _apply_expense_transaction(transaction, report_date, totals, category_totals)
        else:
            _apply_income_transaction(transaction, report_date, totals)
    return totals, category_totals


def _get_month_result(totals: dict[str, float]) -> tuple[str, float]:
    monthly_balance = totals[INCOME_KEY] - totals[EXPENSES_KEY]
    if monthly_balance < 0:
        return "loss", -monthly_balance
    return "profit", monthly_balance


def _category_sort_key(category_total: tuple[str, float]) -> str:
    return category_total[0].lower()


def _build_stats_lines(
    report_date: str,
    totals: dict[str, float],
    category_totals: dict[str, float],
) -> list[str]:
    result_type, result_amount = _get_month_result(totals)
    stats_lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {totals[CAPITAL_KEY]:.2f} rubles",
        f"This month, the {result_type} amounted to {result_amount:.2f} rubles.",
        f"Income: {totals[INCOME_KEY]:.2f} rubles",
        f"Expenses: {totals[EXPENSES_KEY]:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    for index, (category_name, amount) in enumerate(
        sorted(category_totals.items(), key=_category_sort_key),
        start=1,
    ):
        stats_lines.append(f"{index}. {category_name}: {format_amount(amount)}")
    return stats_lines


def stats_handler(report_date: str) -> str:
    date = extract_date(report_date)
    if date is None:
        return INCORRECT_DATE_MSG
    totals, category_totals = _calculate_stats(date)
    return "\n".join(_build_stats_lines(report_date, totals, category_totals))


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
    while True:
        if not process_query():
            break


if __name__ == "__main__":
    main()
