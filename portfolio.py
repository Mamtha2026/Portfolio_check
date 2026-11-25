
import csv


# ==========================================
# 1. READ CSV FILE
# ==========================================

def open_csv(filename):

    with open(filename, "r", newline="", encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        # Remove spaces from column names
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        return list(reader)


# Read your existing CSV
data = open_csv("trades_test.csv")


# Check required CSV columns
required_columns = [
    "portfolio_id",
    "security_id",
    "action",
    "quantity",
    "price",
    "security_type"
]

if not data:
    print("CSV file is empty.")
    raise SystemExit

for column in required_columns:

    if column not in data[0]:
        print("Missing CSV column:", column)
        raise SystemExit


# ==========================================
# 2. DISPLAY TRADES FROM CSV
# ==========================================

print("\n========== PROPOSED TRADES ==========")

for i, row in enumerate(data, start=1):

    print(
        i, "|",
        row["portfolio_id"], "|",
        row["security_id"], "|",
        row["action"], "|",
        row["quantity"], "|",
        row["price"], "|",
        row["security_type"]
    )


# ==========================================
# 3. SELECT TRADE
# ==========================================

try:

    choice = int(input("\nSelect Trade Number: "))

    if choice < 1 or choice > len(data):
        print("Invalid trade selection.")
        raise SystemExit

    selected_trade = data[choice - 1]

except ValueError:

    print("Please enter a valid trade number.")
    raise SystemExit


# Create trade dictionary
trade = {

    "portfolio_id": selected_trade["portfolio_id"].strip(),

    "security_id": selected_trade["security_id"].strip().upper(),

    "action": selected_trade["action"].strip().capitalize(),

    "quantity": selected_trade["quantity"].strip(),

    "price": selected_trade["price"].strip(),

    "security_type": selected_trade["security_type"].strip()
}


# ==========================================
# 4. GET PORTFOLIO REFERENCE DATA FROM USER
# ==========================================

print("\n========== PORTFOLIO REFERENCE DATA ==========")

print("Selected Portfolio:", trade["portfolio_id"])

try:

    cash_balance = float(input("Enter Cash Balance: "))

    restricted_input = input(
        "Enter Restricted Securities (separated by ;): "
    ).strip()

    max_position_pct = float(
        input("Enter Maximum Position Percentage (e.g. 0.30 for 30%): ")
    )

    # Existing holdings
    print("\nEnter Existing Holdings")

    security_ids = input(
        "Enter Holding Security IDs (separated by ;): "
    ).strip()

    quantities = input(
        "Enter Holding Quantities (separated by ;): "
    ).strip()

    market_prices = input(
        "Enter Holding Market Prices (separated by ;): "
    ).strip()

except ValueError:

    print("Invalid portfolio reference data.")
    raise SystemExit


# Convert restricted securities into a list
restricted_securities = [
    security.strip().upper()
    for security in restricted_input.split(";")
    if security.strip()
]


# Create holdings list
holdings = []

if security_ids.strip():

    ids = security_ids.split(";")
    qty = quantities.split(";")
    prices = market_prices.split(";")

    if not (len(ids) == len(qty) == len(prices)):

        print("Error: Holdings data does not match.")
        raise SystemExit

    try:

        for i in range(len(ids)):

            if ids[i].strip():

                holdings.append({

                    "security_id": ids[i].strip().upper(),

                    "quantity": float(qty[i]),

                    "market_price": float(prices[i])

                })

    except ValueError:

        print("Invalid holdings quantity or market price.")
        raise SystemExit


# Create portfolio dictionary
portfolio = {

    "portfolio_id": trade["portfolio_id"],

    "cash_balance": cash_balance,

    "restricted_securities": restricted_securities,

    "max_position_pct": max_position_pct

}


# ==========================================
# VALIDATION 1: VALIDATE TRADE DATA
# ==========================================

def validate_trade(trade):

    try:

        trade["quantity"] = float(trade["quantity"])

        trade["price"] = float(trade["price"])

    except ValueError:

        return "Rejected", "Invalid trade data."

    if (
        trade["quantity"] <= 0
        or trade["price"] <= 0
        or trade["action"] not in ["Buy", "Sell"]
    ):

        return "Rejected", "Invalid trade data."

    return None


# ==========================================
# VALIDATION 2: RESTRICTED SECURITY CHECK
# ==========================================

def check_restricted_security(trade, portfolio):

    restricted_list = portfolio["restricted_securities"]

    if trade["security_id"] in restricted_list:

        return (
            "Rejected",
            "Security is restricted for this portfolio."
        )

    return None


# ==========================================
# VALIDATION 3: SELL HOLDINGS CHECK
# ==========================================

def check_sell_holdings(trade, holdings):

    if trade["action"] == "Sell":

        existing_quantity = 0

        for holding in holdings:

            if holding["security_id"] == trade["security_id"]:

                existing_quantity += holding["quantity"]

        if existing_quantity < trade["quantity"]:

            return (
                "Rejected",
                "Insufficient holdings to sell."
            )

    return None


# ==========================================
# VALIDATION 4: BUY AFFORDABILITY CHECK
# ==========================================

def check_buy_affordability(trade, portfolio):

    if trade["action"] == "Buy":

        trade_cost = trade["quantity"] * trade["price"]

        if trade_cost > portfolio["cash_balance"]:

            return (
                "Rejected",
                "Insufficient cash for this buy order."
            )

    return None


# ==========================================
# VALIDATION 5: POSITION CONCENTRATION CHECK
# ==========================================

def check_position_concentration(trade, portfolio, holdings):

    if trade["action"] == "Buy":

        # Step 1: Post trade cash
        trade_cost = trade["quantity"] * trade["price"]

        post_trade_cash = portfolio["cash_balance"] - trade_cost

        # Step 2: Existing quantity of this security
        existing_quantity = 0

        for holding in holdings:

            if holding["security_id"] == trade["security_id"]:

                existing_quantity += holding["quantity"]

        post_trade_quantity = existing_quantity + trade["quantity"]

        # Step 3: Value of this security
        post_trade_value = post_trade_quantity * trade["price"]

        # Step 4: Value of all other holdings
        value_of_other_holdings = 0

        for holding in holdings:

            if holding["security_id"] != trade["security_id"]:

                value = holding["quantity"] * holding["market_price"]

                value_of_other_holdings += value

        # Step 5: Total portfolio value
        total_portfolio_value = (
            post_trade_cash
            + post_trade_value
            + value_of_other_holdings
        )

        # Step 6: Position percentage
        if total_portfolio_value <= 0:

            position_pct = float("inf")

        else:

            position_pct = post_trade_value / total_portfolio_value

        # Step 7: Compare with maximum position percentage
        if position_pct > portfolio["max_position_pct"]:

            return (
                "Needs Manual Sign-off",
                "Exceeds maximum position concentration — requires approval."
            )

    return None


# ==========================================
# VALIDATION 6: APPROVE TRADE
# ==========================================

def approve_trade(trade):

    return (
        "Approved",
        "Trade passed all compliance checks."
    )


# ==========================================
# 5. MAIN FUNCTION: PROCESS TRADE
# ==========================================

def process_trade(trade, portfolio, holdings):

    # Run validations in the required order

    validations = [

        lambda: validate_trade(trade),

        lambda: check_restricted_security(trade, portfolio),

        lambda: check_sell_holdings(trade, holdings),

        lambda: check_buy_affordability(trade, portfolio),

        lambda: check_position_concentration(
            trade, portfolio, holdings
        )

    ]

    for validation in validations:

        result = validation()

        if result is not None:

            return result

    # Validation 6: Approve
    return approve_trade(trade)


# ==========================================
# 6. DISPLAY FINAL RESULT
# ==========================================

decision, reason = process_trade(trade, portfolio, holdings)

print("\n========== TRADE COMPLIANCE RESULT ==========")

print("Portfolio ID  :", trade["portfolio_id"])

print("Security ID   :", trade["security_id"])

print("Action        :", trade["action"])

print("Quantity      :", trade["quantity"])

print("Price         :", trade["price"])

print("Security Type :", trade["security_type"])

print("---------------------------------------------")

print("Decision      :", decision)

print("Reason        :", reason)

print("=============================================")
