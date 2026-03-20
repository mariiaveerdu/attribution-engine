with raw_data as (
    -- Traemos los datos de la "semilla" cargada
    select * from {{ ref('raw_web_traffic') }}
),

cleaned as (
    select
        -- 1. Quitamos duplicados basados en el ID de sesión
        -- Usamos distinct para asegurar registros únicos
        distinct
        session_id,
        user_id,
        
        -- 2. Limpieza de fechas
        -- try_cast es Senior: si la fecha está rota, devuelve NULL en vez de romper el proceso
        try_cast(session_at as timestamp) as session_at,
        
        -- 3. Normalización de canales
        -- Si es nulo, le asignamos 'direct'
        lower(coalesce(utm_source, 'direct')) as utm_source
        
    from raw_data
)

select * from cleaned