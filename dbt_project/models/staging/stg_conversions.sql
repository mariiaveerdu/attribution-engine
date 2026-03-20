with raw_data as (
    select * from {{ ref('raw_conversions') }}
),

cleaned as (
    select
        order_id,
        user_id,
        try_cast(converted_at as timestamp) as converted_at,
        
        -- Convertimos el texto a número decimal
        cast(revenue as decimal(10,2)) as revenue_amount
    from raw_data
)

select * from cleaned