-- ============================================
-- Supabase Database Functions
-- ============================================
-- Run these in your Supabase SQL Editor to enable schema discovery
-- Source: https://www.linkedin.com/pulse/supabase-issues-craig-stevenson-ugohe

-- Get all tables in the public schema
CREATE OR REPLACE FUNCTION get_tables()
RETURNS text[] AS $$
BEGIN
  RETURN (
    SELECT array_agg(t.table_name::text)
    FROM information_schema.tables AS t
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get column information for a specific table
CREATE OR REPLACE FUNCTION get_table_columns(table_name_param TEXT)
RETURNS TABLE(
    column_name TEXT,
    data_type TEXT,
    is_nullable BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.column_name::TEXT,
    c.data_type::TEXT,
    c.is_nullable::BOOLEAN
  FROM information_schema.columns AS c
  WHERE c.table_schema = 'public'
  AND c.table_name = table_name_param
  ORDER BY c.ordinal_position;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get row count for a specific table
CREATE OR REPLACE FUNCTION get_table_count(table_name_param TEXT)
RETURNS BIGINT AS $$
BEGIN
  DECLARE
    result BIGINT;
  BEGIN
    EXECUTE format('SELECT COUNT(*) FROM %I', table_name_param) INTO result;
    RETURN result;
  EXCEPTION WHEN OTHERS THEN
    RETURN -1;
  END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_tables() TO authenticated;
GRANT EXECUTE ON FUNCTION get_table_columns(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_table_count(TEXT) TO authenticated;
