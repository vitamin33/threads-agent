
-- Check latest achievements with business value
SELECT 
  id,
  title,
  business_value,
  time_saved_hours,
  performance_improvement_pct,
  created_at
FROM achievements 
WHERE business_value IS NOT NULL 
ORDER BY id DESC 
LIMIT 5;
