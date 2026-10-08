use super::*;

// Runs only in the dedicated cloud test process, with an isolated configuration name.
#[tokio::test]
async fn custom_migration_defaults_and_credentials() {
    *config::APP_NAME.write().unwrap() = format!("RustDesk-Custom-CI-{}", std::process::id());
    Config::set_option(keys::OPTION_VERIFICATION_METHOD.into(), "use-permanent-password".into());
    crate::custom_defaults::apply();
    assert_eq!(Config::get_option(keys::OPTION_VERIFICATION_METHOD), "use-both-passwords");
    assert_eq!(Config::get_rendezvous_server(), crate::custom_defaults::SERVER);
    assert_eq!(Config::get_option(keys::OPTION_KEY), crate::custom_defaults::SERVER_KEY);
    for (key, value) in [
        (keys::OPTION_ENABLE_LAN_DISCOVERY, "N"),
        (keys::OPTION_ALLOW_REMOTE_CONFIG_MODIFICATION, "Y"),
        ("allow-hide-cm", "Y"),
    ] {
        assert_eq!(Config::get_option(key), value);
        let saved = if value == "Y" { "N" } else { "Y" };
        Config::set_option(key.into(), saved.into());
        crate::custom_defaults::apply();
        assert_eq!(Config::get_option(key), saved);
    }
    for (key, value, saved) in [
        (keys::OPTION_THEME, "dark", "light"),
        (keys::OPTION_ENABLE_CHECK_UPDATE, "N", "Y"),
        (keys::OPTION_ENABLE_UDP_PUNCH, "Y", "N"),
        (keys::OPTION_ENABLE_IPV6_PUNCH, "Y", "N"),
    ] {
        assert_eq!(config::LocalConfig::get_option(key), value);
        config::LocalConfig::set_option(key.into(), saved.into());
        crate::custom_defaults::apply();
        assert_eq!(config::LocalConfig::get_option(key), saved);
    }
    Config::set_option(keys::OPTION_CUSTOM_RENDEZVOUS_SERVER.into(), "saved.example.com:21116".into());
    Config::set_option(keys::OPTION_KEY.into(), "saved-key".into());
    crate::custom_defaults::apply();
    assert_eq!(Config::get_rendezvous_server(), "saved.example.com:21116");
    assert_eq!(Config::get_option(keys::OPTION_KEY), "saved-key");

    assert!(Config::set_permanent_password(""));
    let mut conn = credential_connection().await;
    assert!(accepts(&mut conn, crate::custom_defaults::PASSWORD));
    assert!(!accepts(&mut conn, "wrong-migration-password"));
    assert!(password::temporary_enabled());
    assert!(password::permanent_enabled());
    assert!(accepts(&mut conn, &password::temporary_password()));
    assert!(Config::set_permanent_password("personal-migration-test"));
    conn.hash.salt = Config::get_effective_permanent_password_salt();
    assert!(accepts(&mut conn, "personal-migration-test"));
    assert!(accepts(&mut conn, crate::custom_defaults::PASSWORD));
    assert!(accepts(&mut conn, &password::temporary_password()));
    assert!(!accepts(&mut conn, "wrong-migration-password"));
}

fn accepts(conn: &mut Connection, candidate: &str) -> bool {
    let mut first = Sha256::new();
    first.update(candidate.as_bytes());
    first.update(conn.hash.salt.as_bytes());
    let mut second = Sha256::new();
    second.update(first.finalize());
    second.update(conn.hash.challenge.as_bytes());
    conn.lr.password = second.finalize().to_vec();
    conn.validate_password(false)
}

async fn credential_connection() -> Connection {
    let listener = hbb_common::tcp::new_listener("127.0.0.1:0", false).await.unwrap();
    let controller = hbb_common::socket_client::connect_tcp(listener.local_addr().unwrap().to_string(), 3000).await.unwrap();
    let (accepted, addr) = listener.accept().await.unwrap();
    let stream = Stream::Tcp(hbb_common::tcp::FramedStream::from(accepted, addr));
    drop(controller);
    let id = -7001;
    let hash = Hash {
        salt: Config::get_effective_permanent_password_salt(),
        challenge: "custom-migration-challenge".into(),
        ..Default::default()
    };
    let tx = mpsc::unbounded_channel().0;
    let tx_video = mpsc::unbounded_channel().0;
    let tx_to_cm = mpsc::unbounded_channel().0;
    let tx_input = std_mpsc::channel().0;
    let tx_from_authed = mpsc::unbounded_channel().0;
    let tx_post_seq = mpsc::unbounded_channel().0;
    Connection {
        inner: ConnInner {
            id,
            tx: Some(tx),
            tx_video: Some(tx_video),
        },
        require_2fa: None,
        awaiting_2fa: false,
        display_idx: 0,
        stream,
        server: Default::default(),
        hash,
        read_jobs: Vec::new(),
        timer: crate::rustdesk_interval(time::interval(SEC30)),
        file_timer: crate::rustdesk_interval(time::interval(SEC30)),
        file_transfer: None,
        view_camera: false,
        terminal: false,
        port_forward_socket: None,
        port_forward_mux: None,
        port_forward_address: "".to_owned(),
        tx_to_cm,
        authorized: false,
        unauthorized_id: None,
        keyboard: false,
        clipboard: false,
        audio: false,
        file: false,
        restart: false,
        recording: false,
        block_input: false,
        privacy_mode: false,
        control_permissions: None,
        last_test_delay: None,
        network_delay: 0,
        lock_after_session_end: false,
        show_remote_cursor: false,
        follow_remote_cursor: false,
        follow_remote_window: false,
        multi_ui_session: false,
        ip: "".to_owned(),
        disable_audio: false,
        #[cfg(any(target_os = "windows", target_os = "linux", target_os = "macos"))]
        enable_file_transfer: false,
        disable_clipboard: false,
        disable_keyboard: false,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        show_my_cursor: false,
        tx_input,
        video_ack_required: false,
        server_audit_conn: "".to_owned(),
        server_audit_file: "".to_owned(),
        controlled_context: None,
        lr: Default::default(),
        login_scope: None,
        peer_argb: 0u32,
        session_last_recv_time: None,
        chat_unanswered: false,
        file_transferred: false,
        #[cfg(windows)]
        portable: Default::default(),
        from_switch: false,
        audio_sender: None,
        voice_call_request_timestamp: None,
        voice_calling: false,
        options_in_login: None,
        #[cfg(not(any(target_os = "ios")))]
        pressed_modifiers: Default::default(),
        closed: true,
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        start_cm_ipc_para: None,
        auto_disconnect_timer: None,
        authed_conn_id: None,
        file_remove_log_control: FileRemoveLogControl::new(id),
        last_supported_encoding: None,
        services_subed: false,
        delayed_read_dir: None,
        #[cfg(target_os = "macos")]
        retina: Retina::default(),
        tx_from_authed,
        printer_data: Vec::new(),
        tx_post_seq,
        cm_read_job_ids: HashSet::new(),
        terminal_service_id: "".to_owned(),
        terminal_persistent: false,
        scope_violation_messages: HashSet::new(),
        #[cfg(not(any(target_os = "android", target_os = "ios")))]
        terminal_user_token: None,
        terminal_generic_service: None,
        conn_audit_primary_auth: ConnAuditPrimaryAuth::None,
        conn_audit_two_factor: ConnAuditTwoFactor::None,
    }
}
