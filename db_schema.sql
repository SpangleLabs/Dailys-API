CREATE TABLE IF NOT EXISTS dailys_data (
    "stat_name" text NOT NULL,
    "stat_date" date NOT NULL,
    "source"    text NOT NULL,
    "stat_data" jsonb NOT NULL
);

ALTER TABLE "dailys_data"
ADD CONSTRAINT "dailys_data_stat_name_stat_date" UNIQUE ("stat_name", "stat_date");

CREATE TABLE IF NOT EXISTS dailys_static (
    "stat_name" text UNIQUE NOT NULL,
    "source"    text NOT NULL,
    "stat_data" jsonb NOT NULL
);
