CREATE TABLE works (id TEXT PRIMARY KEY, title TEXT, year INT);
CREATE TABLE authors (work_id TEXT, author_id TEXT);
CREATE TABLE citations (citing_id TEXT, cited_id TEXT);
