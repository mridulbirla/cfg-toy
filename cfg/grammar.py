import textwrap

# ClickHouse CFG Grammar using Lark syntax
CLICKHOUSE_GRAMMAR = textwrap.dedent(r"""
    // ---------- Punctuation & operators ----------
    SP: " "
    COMMA: ","
    GT: ">"
    LT: "<"
    GTE: ">="
    LTE: "<="
    EQ: "="
    NEQ: "!="
    SEMI: ";"
    LPAREN: "("
    RPAREN: ")"
    ASTERISK: "*"

    // ---------- Keywords ----------
    SELECT: "SELECT"
    FROM: "FROM"
    WHERE: "WHERE"
    GROUP: "GROUP"
    BY: "BY"
    ORDER: "ORDER"
    LIMIT: "LIMIT"
    AND: "AND"
    OR: "OR"
    ASC: "ASC"
    DESC: "DESC"
    INTERVAL: "INTERVAL"
    NOW: "NOW()"
    HOUR: "HOUR"
    DAY: "DAY"
    WEEK: "WEEK"
    MONTH: "MONTH"
    YEAR: "YEAR"

    // ---------- Aggregate Functions ----------
    COUNT: "COUNT"
    SUM: "SUM"
    AVG: "AVG"
    MAX: "MAX"
    MIN: "MIN"

    // ---------- Start ----------
    start: select_statement SEMI

    // ---------- Select Statement ----------
    select_statement: SELECT SP select_list SP FROM SP table_name (SP where_clause)? (SP group_clause)? (SP order_clause)? (SP limit_clause)?

    // ---------- Select List ----------
    select_list: aggregate_function | column_list | group_select_list
    aggregate_function: COUNT LPAREN ASTERISK RPAREN | aggregate_func_name LPAREN column_name RPAREN
    aggregate_func_name: SUM | AVG | MAX | MIN
    column_list: column_name (COMMA SP column_name)*
    group_select_list: column_name COMMA SP aggregate_func_name LPAREN column_name RPAREN

    // ---------- Tables ----------
    table_name: "orders" | "customers" | "products"

    // ---------- Where Clause ----------
    where_clause: WHERE SP condition (SP (AND | OR) SP condition)*
    condition: column_name SP comparison_operator SP value | column_name SP "IN" SP LPAREN value_list RPAREN | time_condition
    comparison_operator: EQ | NEQ | GT | LT | GTE | LTE
    value: string_literal | number_literal | "NULL"
    value_list: value (COMMA SP value)*

    // ---------- Time Conditions ----------
    time_condition: column_name SP GTE SP NOW SP "-" SP INTERVAL SP number_literal SP time_unit | column_name SP LTE SP NOW SP "-" SP INTERVAL SP number_literal SP time_unit
    time_unit: HOUR | DAY | WEEK | MONTH | YEAR

    // ---------- Group Clause ----------
    group_clause: GROUP SP BY SP column_name (COMMA SP column_name)*

    // ---------- Order Clause ----------
    order_clause: ORDER SP BY SP column_name SP (ASC | DESC)?

    // ---------- Limit Clause ----------
    limit_clause: LIMIT SP number_literal

    // ---------- Columns ----------
    column_name: "id" | "customer_id" | "product_id" | "order_date" | "total_amount" | "status" | "created_at" | "updated_at" | "name" | "email" | "price" | "category"

    // ---------- Terminals ----------
    string_literal: /'[A-Za-z0-9_ ]*'/
    number_literal: /[0-9]+(\.[0-9]+)?/
""")
