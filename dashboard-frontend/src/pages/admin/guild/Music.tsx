import { useCallback, useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useOutletContext } from 'react-router-dom';
import api from '../../../lib/api';

// Discord IDs stay strings end-to-end: they exceed JS number precision.
interface MusicSettings {
  dj_role_id: string | null;
  vote_ratio: number;
  stay_247: boolean;
  stay_channel_id: string | null;
  default_volume: number;
  request_channel_id: string | null;
  request_message_id: string | null;
  stage_announce: boolean;
}

interface Option {
  id: string;
  name: string;
}

interface MusicData {
  settings: MusicSettings;
  roles: Option[];
  text_channels: Option[];
  voice_channels: Option[];
  warning?: string;
}

interface GuildContext {
  guildId: string;
}

/** Editable form state; '' means "none" for the selects. */
interface MusicForm {
  djRoleId: string;
  votePercent: number;
  defaultVolume: number;
  stay247: boolean;
  stayChannelId: string;
  requestChannelId: string;
  stageAnnounce: boolean;
}

type Message = { text: string; type: 'success' | 'warning' | 'error' };

const BASE_INPUT: CSSProperties = {
  width: '100%',
  padding: '0.5rem 0.75rem',
  background: 'rgba(15, 23, 42, 0.6)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text-primary)',
  fontSize: '0.875rem',
  outline: 'none',
  boxSizing: 'border-box',
  cursor: 'pointer',
};

const SECTION_TITLE: CSSProperties = {
  fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase',
  letterSpacing: '0.08em', color: 'var(--color-text-muted)', marginBottom: '1rem',
  display: 'flex', alignItems: 'center', gap: '0.5rem',
};

const MESSAGE_COLORS: Record<Message['type'], string> = {
  success: 'var(--color-accent-emerald)',
  warning: 'var(--color-accent-amber)',
  error: 'var(--color-accent-rose)',
};

const MESSAGE_ICONS: Record<Message['type'], string> = {
  success: '✅',
  warning: '⚠️',
  error: '❌',
};

function toForm(data: MusicData): MusicForm {
  const s = data.settings;
  const has = (list: Option[], id: string | null) => (id && list.some(o => o.id === id) ? id : '');
  return {
    djRoleId: has(data.roles, s.dj_role_id),
    votePercent: Math.round(s.vote_ratio * 100),
    defaultVolume: s.default_volume,
    stay247: s.stay_247,
    stayChannelId: has(data.voice_channels, s.stay_channel_id),
    requestChannelId: has(data.text_channels, s.request_channel_id),
    stageAnnounce: s.stage_announce,
  };
}

/** Builds a partial PUT body holding only the fields that changed. */
function diffBody(initial: MusicForm, form: MusicForm): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if (form.djRoleId !== initial.djRoleId) body.dj_role_id = form.djRoleId || null;
  if (form.votePercent !== initial.votePercent) body.vote_ratio = form.votePercent / 100;
  if (form.defaultVolume !== initial.defaultVolume) body.default_volume = form.defaultVolume;
  if (form.stageAnnounce !== initial.stageAnnounce) body.stage_announce = form.stageAnnounce;
  if (form.requestChannelId !== initial.requestChannelId) body.request_channel_id = form.requestChannelId || null;
  if (form.stay247 !== initial.stay247) body.stay_247 = form.stay247;
  if (form.stayChannelId !== initial.stayChannelId || (form.stay247 && !initial.stay247)) {
    body.stay_channel_id = form.stayChannelId || null;
  }
  return body;
}

// ─── Small building blocks ────────────────────────────────────────────

function Toggle({
  checked,
  onChange,
  disabled,
  color = 'var(--color-accent-blue)',
}: {
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
  color?: string;
}) {
  return (
    <div
      role="switch"
      aria-checked={checked}
      onClick={disabled ? undefined : onChange}
      style={{
        width: 40, height: 22, borderRadius: 11, flexShrink: 0,
        background: checked ? color : 'var(--color-border)',
        position: 'relative',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'background 0.18s',
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <motion.div
        animate={{ x: checked ? 20 : 2 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        style={{
          position: 'absolute', top: 3,
          width: 16, height: 16, borderRadius: '50%',
          background: 'white',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }}
      />
    </div>
  );
}

function FieldLabel({ title, note, htmlFor }: { title: string; note?: string; htmlFor?: string }) {
  return (
    <div style={{ marginBottom: '0.5rem' }}>
      <label htmlFor={htmlFor} style={{ fontSize: '0.875rem', fontWeight: 500, display: 'block' }}>{title}</label>
      {note && (
        <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '0.1rem' }}>{note}</p>
      )}
    </div>
  );
}

function ToggleRow({
  title, note, checked, onChange, disabled, color,
}: {
  title: string;
  note: string;
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
  color?: string;
}) {
  return (
    <motion.div
      onClick={disabled ? undefined : onChange}
      whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.04)' }}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem',
        cursor: disabled ? 'default' : 'pointer',
        padding: '0.625rem 0.75rem', margin: '-0.625rem -0.75rem', borderRadius: 'var(--radius-md)',
        transition: 'background 0.2s',
      }}
    >
      <div>
        <p style={{ fontSize: '0.875rem', fontWeight: 500 }}>{title}</p>
        <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '0.1rem' }}>{note}</p>
      </div>
      <Toggle checked={checked} onChange={onChange} disabled={disabled} color={color} />
    </motion.div>
  );
}

function PercentSlider({
  id, value, min, max, onChange, disabled,
}: {
  id: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ flex: 1, accentColor: 'var(--color-accent-blue)', cursor: disabled ? 'not-allowed' : 'pointer' }}
      />
      <span style={{
        minWidth: '3.25rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: 600,
        fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)',
      }}>
        {value}%
      </span>
    </div>
  );
}

function OptionSelect({
  id, value, options, onChange, emptyLabel, prefix = '', disabled,
}: {
  id: string;
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  emptyLabel: string;
  prefix?: string;
  disabled?: boolean;
}) {
  return (
    <select
      id={id}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
      style={{ ...BASE_INPUT, opacity: disabled ? 0.6 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
    >
      <option value="" style={{ background: '#0f172a' }}>{emptyLabel}</option>
      {options.map(o => (
        <option key={o.id} value={o.id} style={{ background: '#0f172a' }}>{prefix}{o.name}</option>
      ))}
    </select>
  );
}

function Section({ icon, title, children, delay = 0 }: { icon: string; title: string; children: ReactNode; delay?: number }) {
  return (
    <motion.div
      className="glass-card"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      style={{ padding: '1.25rem' }}
    >
      <h4 style={SECTION_TITLE}>
        <span>{icon}</span>
        {title}
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.125rem' }}>
        {children}
      </div>
    </motion.div>
  );
}

const Divider = () => <div style={{ height: 1, background: 'var(--color-border)' }} />;

// ─── Main page ────────────────────────────────────────────────────────

export default function GuildMusic() {
  const { guildId } = useOutletContext<GuildContext>();
  const { t } = useTranslation();
  const [data, setData] = useState<MusicData | null>(null);
  const [initial, setInitial] = useState<MusicForm | null>(null);
  const [form, setForm] = useState<MusicForm | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const messageTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (messageTimerRef.current !== null) clearTimeout(messageTimerRef.current);
    };
  }, []);

  const applyData = useCallback((next: MusicData) => {
    const nextForm = toForm(next);
    setData(next);
    setInitial(nextForm);
    setForm(nextForm);
  }, []);

  useEffect(() => {
    api.get(`/api/guild/${guildId}/music`)
      .then(({ data }) => {
        applyData(data);
        setLoadError(null);
      })
      .catch((err) => {
        setLoadError(err?.response?.status === 503 ? t('music.unavailable') : t('music.loadError'));
      })
      .finally(() => setLoading(false));
  }, [guildId, applyData, t]);

  const showMessage = (next: Message) => {
    setMessage(next);
    if (messageTimerRef.current !== null) clearTimeout(messageTimerRef.current);
    messageTimerRef.current = setTimeout(() => setMessage(null), next.type === 'success' ? 4000 : 8000);
  };

  const update = <K extends keyof MusicForm>(key: K, value: MusicForm[K]) => {
    setForm(prev => (prev ? { ...prev, [key]: value } : prev));
  };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
      <div className="animate-pulse-glow">🎵</div>
    </div>
  );

  if (loadError || !data || !form || !initial) return (
    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-muted)' }}>
      <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🎵</div>
      <p style={{ fontSize: '0.875rem' }}>{loadError ?? t('music.loadError')}</p>
    </div>
  );

  const body = diffBody(initial, form);
  const dirty = Object.keys(body).length > 0;

  const handleSave = async () => {
    if (form.stay247 && !form.stayChannelId) {
      showMessage({ text: t('music.stayChannelRequired'), type: 'error' });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const { data: next } = await api.put<MusicData>(`/api/guild/${guildId}/music`, body);
      applyData(next);
      showMessage(next.warning
        ? { text: t('music.joinWarning'), type: 'warning' }
        : { text: t('music.saved'), type: 'success' });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        t('music.saveError');
      showMessage({ text: detail, type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 760 }}>
      {/* Header */}
      <motion.div
        className="glass-card"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ padding: '1.25rem 1.5rem', marginBottom: '1.25rem' }}
      >
        <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
          🎵 {t('music.title')}
        </h2>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          {t('music.subtitle')}
        </p>
      </motion.div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* DJ & voting */}
        <Section icon="🎧" title={t('music.djSection')}>
          <div>
            <FieldLabel htmlFor="music-dj-role" title={t('music.djRole')} note={t('music.djRoleNote')} />
            <OptionSelect
              id="music-dj-role"
              value={form.djRoleId}
              options={data.roles}
              onChange={(v) => update('djRoleId', v)}
              emptyLabel={t('music.noDjRole')}
              prefix="@"
              disabled={saving}
            />
          </div>
          <Divider />
          <div style={{ opacity: form.djRoleId ? 1 : 0.6 }}>
            <FieldLabel htmlFor="music-vote-ratio" title={t('music.voteRatio')} note={t('music.voteRatioNote')} />
            <PercentSlider
              id="music-vote-ratio"
              min={10}
              max={100}
              value={form.votePercent}
              onChange={(v) => update('votePercent', v)}
              disabled={saving}
            />
          </div>
        </Section>

        {/* Playback */}
        <Section icon="🔊" title={t('music.playbackSection')} delay={0.05}>
          <div>
            <FieldLabel htmlFor="music-volume" title={t('music.defaultVolume')} note={t('music.defaultVolumeNote')} />
            <PercentSlider
              id="music-volume"
              min={0}
              max={100}
              value={form.defaultVolume}
              onChange={(v) => update('defaultVolume', v)}
              disabled={saving}
            />
          </div>
          <Divider />
          <ToggleRow
            title={t('music.stageAnnounce')}
            note={t('music.stageAnnounceNote')}
            checked={form.stageAnnounce}
            onChange={() => update('stageAnnounce', !form.stageAnnounce)}
            disabled={saving}
            color="var(--color-accent-violet)"
          />
        </Section>

        {/* 24/7 */}
        <Section icon="🌙" title={t('music.staySection')} delay={0.1}>
          <ToggleRow
            title={t('music.stay247')}
            note={t('music.stay247Note')}
            checked={form.stay247}
            onChange={() => update('stay247', !form.stay247)}
            disabled={saving}
            color="var(--color-accent-emerald)"
          />
          <div>
            <FieldLabel htmlFor="music-stay-channel" title={t('music.stayChannel')} note={t('music.stayChannelNote')} />
            <OptionSelect
              id="music-stay-channel"
              value={form.stayChannelId}
              options={data.voice_channels}
              onChange={(v) => update('stayChannelId', v)}
              emptyLabel={t('music.selectVoiceChannel')}
              prefix="🔊 "
              disabled={saving}
            />
            {form.stay247 && !form.stayChannelId && (
              <p style={{ fontSize: '0.72rem', color: 'var(--color-accent-amber)', marginTop: '0.375rem' }}>
                ⚠️ {t('music.stayChannelRequired')}
              </p>
            )}
          </div>
        </Section>

        {/* Request channel */}
        <Section icon="📮" title={t('music.requestSection')} delay={0.15}>
          <div>
            <FieldLabel htmlFor="music-request-channel" title={t('music.requestChannel')} note={t('music.requestChannelNote')} />
            <OptionSelect
              id="music-request-channel"
              value={form.requestChannelId}
              options={data.text_channels}
              onChange={(v) => update('requestChannelId', v)}
              emptyLabel={t('music.noRequestChannel')}
              prefix="# "
              disabled={saving}
            />
          </div>
        </Section>

        {/* Save bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            flexWrap: 'wrap',
            paddingTop: '0.25rem',
          }}
        >
          {message ? (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              style={{ fontSize: '0.8125rem', color: MESSAGE_COLORS[message.type], flex: 1, minWidth: 0 }}
            >
              {MESSAGE_ICONS[message.type]} {message.text}
            </motion.span>
          ) : (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              {dirty ? t('music.unsaved') : ''}
            </span>
          )}
          <button
            className="btn-gradient"
            onClick={handleSave}
            disabled={saving || !dirty}
            style={{ opacity: saving || !dirty ? 0.6 : 1, cursor: saving || !dirty ? 'not-allowed' : 'pointer' }}
          >
            {saving ? t('common.saving') : `💾 ${t('common.save')}`}
          </button>
        </div>
      </div>
    </div>
  );
}
