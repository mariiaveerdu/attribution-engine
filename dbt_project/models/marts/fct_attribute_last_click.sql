with joined_data as (
    select * from {{ ref('int_session_conversions_joined') }}
),

last_click_assigned as (
    select
        *,
        -- Numeramos los clics de cada venta, del más reciente al más antiguo
        row_number() over (
            partition by order_id 
            order by session_at desc
        ) as click_priority
    from joined_data
)

select
    order_id,
    session_id,
    user_id,
    converted_at,
    utm_source as winning_channel,
    revenue_amount
from last_click_assigned
where click_priority = 1 -- Solo nos quedamos con el último clic