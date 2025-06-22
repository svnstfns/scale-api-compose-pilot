# table_definitions.py

table_definitions = {
    "section_status": """
        CREATE TABLE IF NOT EXISTS section_status (
            section_path TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "file_counts": """
        CREATE TABLE IF NOT EXISTS file_counts (
            share_name TEXT PRIMARY KEY,
            total_files INTEGER,
            total_directories INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "inventory": """
        CREATE TABLE IF NOT EXISTS inventory (
            file_id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            mimetype TEXT,
            size INTEGER,
            size_hr TEXT,
            checksum TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(filepath)
        )
    """,
    "error_log": """
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            issue TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_path)
        )
    """,
    "conversion_queue": """
        CREATE TABLE IF NOT EXISTS conversion_queue (
            filepath TEXT PRIMARY KEY,
            target_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "duplicates": """
        CREATE TABLE IF NOT EXISTS duplicates (
            checksum TEXT PRIMARY KEY,
            duplicate_count INTEGER DEFAULT 0
        )
    """,
    "video_properties": """
        CREATE TABLE IF NOT EXISTS video_properties (
            file_path TEXT NOT NULL,
            checksum TEXT PRIMARY KEY,
            codec_name TEXT,
            resolution TEXT,
            quality TEXT,
            duration TEXT,
            result TEXT
        )
    """,
    "sections": """
        CREATE TABLE IF NOT EXISTS sections (
            path TEXT PRIMARY KEY
        )
    """
}
