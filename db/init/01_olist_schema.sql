CREATE TABLE IF NOT EXISTS olist_customers (
    customer_id              VARCHAR PRIMARY KEY,
    customer_unique_id       VARCHAR,
    customer_zip_code_prefix VARCHAR,
    customer_city            VARCHAR,
    customer_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS olist_orders (
    order_id                      VARCHAR PRIMARY KEY,
    customer_id                   VARCHAR,
    order_status                  VARCHAR,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS olist_order_items (
    order_id            VARCHAR,
    order_item_id       INTEGER,
    product_id          VARCHAR,
    seller_id           VARCHAR,
    shipping_limit_date TIMESTAMP,
    price               NUMERIC,
    freight_value       NUMERIC
);

CREATE TABLE IF NOT EXISTS olist_order_payments (
    order_id             VARCHAR,
    payment_sequential   INTEGER,
    payment_type         VARCHAR,
    payment_installments INTEGER,
    payment_value        NUMERIC
);

CREATE TABLE IF NOT EXISTS olist_order_reviews (
    review_id               VARCHAR,
    order_id                VARCHAR,
    review_score            INTEGER,
    review_comment_title    VARCHAR,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS olist_products (
    product_id                 VARCHAR PRIMARY KEY,
    product_category_name      VARCHAR,
    product_name_lenght        INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           NUMERIC,
    product_length_cm          NUMERIC,
    product_height_cm          NUMERIC,
    product_width_cm           NUMERIC
);

CREATE TABLE IF NOT EXISTS olist_sellers (
    seller_id              VARCHAR PRIMARY KEY,
    seller_zip_code_prefix VARCHAR,
    seller_city            VARCHAR,
    seller_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS olist_geolocation (
    geolocation_zip_code_prefix VARCHAR,
    geolocation_lat             NUMERIC,
    geolocation_lng             NUMERIC,
    geolocation_city            VARCHAR,
    geolocation_state           VARCHAR
);

CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name         VARCHAR PRIMARY KEY,
    product_category_name_english VARCHAR
);
