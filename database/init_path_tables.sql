-- Create ENUM types for Path Management
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'data_source_type') THEN
        CREATE TYPE data_source_type AS ENUM ('MANUAL', 'AUTOMATED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'segment_status_type') THEN
        CREATE TYPE segment_status_type AS ENUM ('OPTIMAL', 'MEDIUM', 'SUFFICIENT', 'REQUIRES_MAINTENANCE');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'obstacle_type') THEN
        CREATE TYPE obstacle_type AS ENUM ('POTHOLE', 'ROUGH_SURFACE', 'DEBRIS', 'CONSTRUCTION', 'OTHER');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'obstacle_severity_type') THEN
        CREATE TYPE obstacle_severity_type AS ENUM ('MINOR', 'MODERATE', 'SEVERE');
    END IF;
END $$;

-- Table: PathInfo
CREATE TABLE IF NOT EXISTS PathInfo (
    path_info_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,  -- References user_id from User Management Service (no FK constraint across services)
    name VARCHAR(255),
    description TEXT,
    data_source data_source_type NOT NULL DEFAULT 'MANUAL',
    publishable BOOLEAN NOT NULL DEFAULT FALSE,
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: Segments
CREATE TABLE IF NOT EXISTS Segments (
    segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_info_id UUID NOT NULL REFERENCES PathInfo(path_info_id) ON DELETE CASCADE,
    street_name VARCHAR(255),
    status segment_status_type NOT NULL DEFAULT 'OPTIMAL',
    start_latitude NUMERIC(10, 7) NOT NULL,
    start_longitude NUMERIC(10, 7) NOT NULL,
    end_latitude NUMERIC(10, 7) NOT NULL,
    end_longitude NUMERIC(10, 7) NOT NULL,
    segment_order INTEGER NOT NULL,
    length_meters NUMERIC(10, 2) NOT NULL DEFAULT 0
);

-- Table: Obstacles
CREATE TABLE IF NOT EXISTS Obstacles (
    obstacle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id UUID NOT NULL REFERENCES Segments(segment_id) ON DELETE CASCADE,
    type obstacle_type NOT NULL,
    severity obstacle_severity_type NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    description TEXT,
    reported_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pathinfo_user_id ON PathInfo(user_id);
CREATE INDEX IF NOT EXISTS idx_pathinfo_publishable ON PathInfo(publishable);
CREATE INDEX IF NOT EXISTS idx_segments_path_info_id ON Segments(path_info_id);
CREATE INDEX IF NOT EXISTS idx_segments_coordinates ON Segments(start_latitude, start_longitude, end_latitude, end_longitude);
CREATE INDEX IF NOT EXISTS idx_obstacles_segment_id ON Obstacles(segment_id);
CREATE INDEX IF NOT EXISTS idx_obstacles_coordinates ON Obstacles(latitude, longitude);

COMMENT ON TABLE PathInfo IS 'Stores metadata about bike paths entered manually or collected automatically';
COMMENT ON TABLE Segments IS 'Stores individual segments of a path with status and coordinates';
COMMENT ON TABLE Obstacles IS 'Stores obstacles reported on path segments';
