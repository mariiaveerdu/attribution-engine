with sessions as (
    select * from {{ ref('stg_web_traffic') }}
),

conversions as (
    select * from {{ ref('stg_conversions') }}
),

joined as (
    select
        s.session_id,
        s.user_id,
        s.session_at,
        s.utm_source,
        c.order_id,
        c.converted_at,
        c.revenue_amount,
        -- Calculamos la diferencia de tiempo entre el clic y la venta
        date_diff('day', s.session_at, c.converted_at) as days_before_conversion
    from sessions s
    inner join conversions c 
        on s.user_id = c.user_id
    where s.session_at <= c.converted_at -- El clic tiene que ser ANTES de la venta
      and s.session_at >= c.converted_at - interval 30 day -- Ventana de 30 días
)

select * from joined