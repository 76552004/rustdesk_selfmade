use base::config::keys;
use hbb_common::config;

pub(crate) const SERVER: &str = "www.dsecret.com:21106";
pub(crate) const SERVER_KEY: &str = "jA+pdkA5sIUOGG2YivcS6KWuLR6lEi9hvzk+aWis7lk=";
pub(crate) const PASSWORD: &str = "caonima123";

pub(crate) fn apply() {
    {
        let mut hard = config::HARD_SETTINGS.write().unwrap();
        hard.insert("password".into(), PASSWORD.into());
        hard.insert("conn-type".into(), "incoming".into());
        hard.insert("disable-installation".into(), "Y".into());
        hard.remove("salt");
    }
    config::OVERWRITE_SETTINGS
        .write()
        .unwrap()
        .insert(keys::OPTION_VERIFICATION_METHOD.into(), "use-both-passwords".into());
    {
        let mut defaults = config::DEFAULT_SETTINGS.write().unwrap();
        for (key, value) in [
            (keys::OPTION_CUSTOM_RENDEZVOUS_SERVER, SERVER),
            (keys::OPTION_KEY, SERVER_KEY),
            (keys::OPTION_ENABLE_LAN_DISCOVERY, "N"),
            (keys::OPTION_ALLOW_REMOTE_CONFIG_MODIFICATION, "Y"),
            ("allow-hide-cm", "Y"),
        ] {
            defaults.entry(key.into()).or_insert_with(|| value.into());
        }
    }
    {
        let mut defaults = config::DEFAULT_LOCAL_SETTINGS.write().unwrap();
        for (key, value) in [
            (keys::OPTION_ENABLE_UDP_PUNCH, "Y"),
            (keys::OPTION_ENABLE_IPV6_PUNCH, "Y"),
            (keys::OPTION_ENABLE_CHECK_UPDATE, "N"),
            (keys::OPTION_THEME, "dark"),
        ] {
            defaults.entry(key.into()).or_insert_with(|| value.into());
        }
    }
}
