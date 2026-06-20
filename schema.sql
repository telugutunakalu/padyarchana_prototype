-- Padyarchana schema dump
-- Regenerate with: ./venv/bin/python scripts/dump_db.py

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- table: audio_annotations
CREATE TABLE audio_annotations (
	id INTEGER NOT NULL, 
	poem_audio_id INTEGER NOT NULL, 
	word_index INTEGER NOT NULL, 
	word_text VARCHAR(100), 
	timestamp_ms INTEGER, 
	flags JSON, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_audio_id) REFERENCES poem_audio (id) ON DELETE CASCADE
);

-- table: ganas
CREATE TABLE ganas (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	gana_sequence VARCHAR(20) NOT NULL, 
	gana_type VARCHAR(50), 
	syllable_count INTEGER, 
	line_number INTEGER NOT NULL, 
	position_in_line INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id)
);

-- table: meters
CREATE TABLE meters (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	name_english VARCHAR(200), 
	description TEXT, 
	gana_structure JSON, 
	example_pattern VARCHAR(500), 
	PRIMARY KEY (id)
);

-- table: nethra_batches
CREATE TABLE nethra_batches (
	id INTEGER NOT NULL, 
	folder_name VARCHAR(255) NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	total_images INTEGER, 
	annotated_count INTEGER, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id)
);

-- table: nethra_images
CREATE TABLE nethra_images (
	id INTEGER NOT NULL, 
	batch_id INTEGER NOT NULL, 
	filename VARCHAR(500) NOT NULL, 
	image_path VARCHAR(1000) NOT NULL, 
	sort_order INTEGER, 
	ocr_text TEXT, 
	corrected_text TEXT, 
	label VARCHAR(50), 
	annotated_by VARCHAR(100), 
	annotated_at DATETIME, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES nethra_batches (id) ON DELETE CASCADE
);

-- table: poem_audio
CREATE TABLE poem_audio (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	original_filename VARCHAR(255), 
	duration_seconds FLOAT, 
	format VARCHAR(10) NOT NULL, 
	file_size_bytes INTEGER, 
	uploaded_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id) ON DELETE CASCADE
);

-- table: poem_tts_audio
CREATE TABLE poem_tts_audio (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	duration_seconds FLOAT, 
	file_size_bytes INTEGER, 
	voice_description VARCHAR(500), 
	generated_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id) ON DELETE CASCADE
);

-- table: poem_words
CREATE TABLE poem_words (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	word_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	line_number INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id), 
	FOREIGN KEY(word_id) REFERENCES words (id)
);

-- table: poems
CREATE TABLE poems (
	id INTEGER NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	text TEXT NOT NULL, 
	literary_form VARCHAR(100), 
	word_count INTEGER, 
	gana_count INTEGER, 
	line_count INTEGER, 
	poet_id INTEGER, 
	meter_id INTEGER, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP), source VARCHAR(200), prathipadartham JSON, bhavam TEXT, kanda VARCHAR(200), search_text TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poet_id) REFERENCES poets (id), 
	FOREIGN KEY(meter_id) REFERENCES meters (id)
);

-- table: poems_fts
CREATE VIRTUAL TABLE poems_fts USING fts5(
            search_text,
            content='poems',
            content_rowid='id',
            tokenize='trigram'
        );

-- table: poems_fts_config
CREATE TABLE 'poems_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;

-- table: poems_fts_data
CREATE TABLE 'poems_fts_data'(id INTEGER PRIMARY KEY, block BLOB);

-- table: poems_fts_docsize
CREATE TABLE 'poems_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);

-- table: poems_fts_idx
CREATE TABLE 'poems_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;

-- table: poets
CREATE TABLE poets (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	name_english VARCHAR(200), 
	biography TEXT, 
	era VARCHAR(100), 
	birth_year INTEGER, 
	death_year INTEGER, 
	PRIMARY KEY (id)
);

-- table: prasas
CREATE TABLE prasas (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	prasa_type VARCHAR(100), 
	prasa_letters VARCHAR(50), 
	line_number INTEGER NOT NULL, 
	is_compliant BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id)
);

-- table: samasas
CREATE TABLE samasas (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	samasa_text VARCHAR(200) NOT NULL, 
	samasa_type VARCHAR(100), 
	components JSON, 
	position INTEGER, 
	line_number INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id)
);

-- table: sandhis
CREATE TABLE sandhis (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	sandhi_text VARCHAR(200) NOT NULL, 
	sandhi_type VARCHAR(100), 
	first_component VARCHAR(100), 
	second_component VARCHAR(100), 
	position INTEGER, 
	line_number INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id)
);

-- table: tts_batch_jobs
CREATE TABLE tts_batch_jobs (
	id INTEGER NOT NULL, 
	status VARCHAR(20), 
	total_poems INTEGER NOT NULL, 
	completed_poems INTEGER, 
	failed_poems INTEGER, 
	current_poem_id INTEGER, 
	error_log TEXT, 
	started_at DATETIME, 
	completed_at DATETIME, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id)
);

-- table: words
CREATE TABLE words (
	id INTEGER NOT NULL, 
	word VARCHAR(200) NOT NULL, 
	root_form VARCHAR(200), 
	definitions JSON, 
	part_of_speech VARCHAR(50), 
	examples JSON, 
	PRIMARY KEY (id)
);

-- table: yatis
CREATE TABLE yatis (
	id INTEGER NOT NULL, 
	poem_id INTEGER NOT NULL, 
	yati_type VARCHAR(100), 
	yati_position INTEGER NOT NULL, 
	line_number INTEGER NOT NULL, 
	is_compliant BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(poem_id) REFERENCES poems (id)
);

-- index: ix_audio_annotations_id
CREATE INDEX ix_audio_annotations_id ON audio_annotations (id);

-- index: ix_audio_annotations_poem_audio_id
CREATE INDEX ix_audio_annotations_poem_audio_id ON audio_annotations (poem_audio_id);

-- index: ix_ganas_gana_type
CREATE INDEX ix_ganas_gana_type ON ganas (gana_type);

-- index: ix_ganas_id
CREATE INDEX ix_ganas_id ON ganas (id);

-- index: ix_ganas_line_number
CREATE INDEX ix_ganas_line_number ON ganas (line_number);

-- index: ix_ganas_poem_id
CREATE INDEX ix_ganas_poem_id ON ganas (poem_id);

-- index: ix_meters_id
CREATE INDEX ix_meters_id ON meters (id);

-- index: ix_meters_name
CREATE UNIQUE INDEX ix_meters_name ON meters (name);

-- index: ix_nethra_batches_folder_name
CREATE UNIQUE INDEX ix_nethra_batches_folder_name ON nethra_batches (folder_name);

-- index: ix_nethra_batches_id
CREATE INDEX ix_nethra_batches_id ON nethra_batches (id);

-- index: ix_nethra_images_batch_id
CREATE INDEX ix_nethra_images_batch_id ON nethra_images (batch_id);

-- index: ix_nethra_images_id
CREATE INDEX ix_nethra_images_id ON nethra_images (id);

-- index: ix_nethra_images_sort_order
CREATE INDEX ix_nethra_images_sort_order ON nethra_images (sort_order);

-- index: ix_poem_audio_id
CREATE INDEX ix_poem_audio_id ON poem_audio (id);

-- index: ix_poem_audio_poem_id
CREATE UNIQUE INDEX ix_poem_audio_poem_id ON poem_audio (poem_id);

-- index: ix_poem_tts_audio_id
CREATE INDEX ix_poem_tts_audio_id ON poem_tts_audio (id);

-- index: ix_poem_tts_audio_poem_id
CREATE UNIQUE INDEX ix_poem_tts_audio_poem_id ON poem_tts_audio (poem_id);

-- index: ix_poem_words_id
CREATE INDEX ix_poem_words_id ON poem_words (id);

-- index: ix_poem_words_poem_id
CREATE INDEX ix_poem_words_poem_id ON poem_words (poem_id);

-- index: ix_poem_words_word_id
CREATE INDEX ix_poem_words_word_id ON poem_words (word_id);

-- index: ix_poems_id
CREATE INDEX ix_poems_id ON poems (id);

-- index: ix_poems_kanda
CREATE INDEX ix_poems_kanda ON poems (kanda);

-- index: ix_poems_literary_form
CREATE INDEX ix_poems_literary_form ON poems (literary_form);

-- index: ix_poems_meter_id
CREATE INDEX ix_poems_meter_id ON poems (meter_id);

-- index: ix_poems_poet_id
CREATE INDEX ix_poems_poet_id ON poems (poet_id);

-- index: ix_poems_title
CREATE INDEX ix_poems_title ON poems (title);

-- index: ix_poets_era
CREATE INDEX ix_poets_era ON poets (era);

-- index: ix_poets_id
CREATE INDEX ix_poets_id ON poets (id);

-- index: ix_poets_name
CREATE INDEX ix_poets_name ON poets (name);

-- index: ix_prasas_id
CREATE INDEX ix_prasas_id ON prasas (id);

-- index: ix_prasas_poem_id
CREATE INDEX ix_prasas_poem_id ON prasas (poem_id);

-- index: ix_prasas_prasa_type
CREATE INDEX ix_prasas_prasa_type ON prasas (prasa_type);

-- index: ix_samasas_id
CREATE INDEX ix_samasas_id ON samasas (id);

-- index: ix_samasas_poem_id
CREATE INDEX ix_samasas_poem_id ON samasas (poem_id);

-- index: ix_samasas_samasa_type
CREATE INDEX ix_samasas_samasa_type ON samasas (samasa_type);

-- index: ix_sandhis_id
CREATE INDEX ix_sandhis_id ON sandhis (id);

-- index: ix_sandhis_poem_id
CREATE INDEX ix_sandhis_poem_id ON sandhis (poem_id);

-- index: ix_sandhis_sandhi_type
CREATE INDEX ix_sandhis_sandhi_type ON sandhis (sandhi_type);

-- index: ix_tts_batch_jobs_id
CREATE INDEX ix_tts_batch_jobs_id ON tts_batch_jobs (id);

-- index: ix_tts_batch_jobs_status
CREATE INDEX ix_tts_batch_jobs_status ON tts_batch_jobs (status);

-- index: ix_words_id
CREATE INDEX ix_words_id ON words (id);

-- index: ix_words_root_form
CREATE INDEX ix_words_root_form ON words (root_form);

-- index: ix_words_word
CREATE UNIQUE INDEX ix_words_word ON words (word);

-- index: ix_yatis_id
CREATE INDEX ix_yatis_id ON yatis (id);

-- index: ix_yatis_poem_id
CREATE INDEX ix_yatis_poem_id ON yatis (poem_id);

-- index: ix_yatis_yati_type
CREATE INDEX ix_yatis_yati_type ON yatis (yati_type);

-- trigger: poems_fts_ad
CREATE TRIGGER poems_fts_ad AFTER DELETE ON poems BEGIN
            INSERT INTO poems_fts(poems_fts, rowid, search_text)
            VALUES ('delete', old.id, old.search_text);
        END;

-- trigger: poems_fts_ai
CREATE TRIGGER poems_fts_ai AFTER INSERT ON poems BEGIN
            INSERT INTO poems_fts(rowid, search_text)
            VALUES (new.id, new.search_text);
        END;

-- trigger: poems_fts_au
CREATE TRIGGER poems_fts_au AFTER UPDATE ON poems BEGIN
            INSERT INTO poems_fts(poems_fts, rowid, search_text)
            VALUES ('delete', old.id, old.search_text);
            INSERT INTO poems_fts(rowid, search_text)
            VALUES (new.id, new.search_text);
        END;

COMMIT;
PRAGMA foreign_keys = ON;
