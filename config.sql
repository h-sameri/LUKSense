-- INSERT INTO config (env, type, key, value) VALUES ('DEV', NULL, NULL, NULL) ON CONFLICT (env, key) DO NOTHING;
-- INSERT INTO config (env, type, key, value) VALUES ('LIVE', NULL, NULL, NULL) ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'site_name', 'LUKSense Test') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'site_name', 'LUKSense') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'storage_location', '/usr/share/luksense/testnet') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'storage_location', '/usr/share/luksense/mainnet') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'INT', 'row_per_page', '3') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'INT', 'row_per_page', '69') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'index_name', 'testnet_luksense') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'index_name', 'mainnet_luksense') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'registration_status', 'OPEN') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'registration_status', 'CLOSED') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'INT', 'max_result_window', '100') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'INT', 'max_result_window', '10000') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'captcha_status', 'DISABLED') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'captcha_status', 'ENABLED') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'admin_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'admin_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'secret_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'secret_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'csrf_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'csrf_key', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;

INSERT INTO config (env, type, key, value) VALUES ('DEV', 'STR', 'receive_address', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;
INSERT INTO config (env, type, key, value) VALUES ('LIVE', 'STR', 'receive_address', 'MUST_CHANGE_THIS') ON CONFLICT (env, key) DO NOTHING;

-- UPDATE config SET value=NULL WHERE env='DEV' AND key=NULL;
