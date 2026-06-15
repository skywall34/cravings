const LAST_UPDATED = 'May 31, 2026'
const ACCENT = '#E85D04'

interface LegalPageProps {
  doc: 'privacy' | 'terms'
  onBack: () => void
}

export function LegalPage({ doc, onBack }: LegalPageProps) {
  const sections = doc === 'terms' ? TERMS_SECTIONS : PRIVACY_SECTIONS
  const title = doc === 'terms' ? 'Terms of Service' : 'Privacy Policy'

  return (
    <div style={{ width: '100%', maxWidth: 440, margin: '0 auto', padding: '8px 20px 80px' }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#888', fontSize: '0.9rem', padding: 0, marginBottom: 20 }}
      >
        ← Back
      </button>

      <h1 style={{ margin: '0 0 4px', fontSize: '1.7rem', fontWeight: 900, color: '#1A1A1A', letterSpacing: '-0.02em' }}>
        {title}
      </h1>
      <p style={{ margin: '0 0 8px', fontSize: '0.78rem', color: '#888', fontWeight: 600, letterSpacing: '0.02em' }}>
        Last updated {LAST_UPDATED}
      </p>

      {doc === 'terms' && (
        <div style={{
          margin: '14px 0 8px',
          padding: '12px 14px',
          background: 'rgba(245,158,11,0.10)',
          border: '1px solid rgba(245,158,11,0.30)',
          borderRadius: 12,
          fontSize: '0.8rem',
          lineHeight: 1.5,
          color: '#8A6A1F',
          fontWeight: 600,
        }}>
          ⚠️ Cravings suggests food — it does not verify allergens. Dietary tags are best-effort and{' '}
          <strong>not medical advice</strong>. Always confirm ingredients with the restaurant.
        </div>
      )}

      <div style={{ marginTop: 18 }}>
        {sections.map((s, i) => (
          <section key={i} style={{ marginBottom: 26 }}>
            <h2 style={{
              margin: '0 0 8px',
              fontSize: '0.78rem',
              fontWeight: 800,
              color: ACCENT,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}>
              {s.h}
            </h2>
            {s.body.map((para, j) =>
              typeof para === 'string' ? (
                <p key={j} style={{ margin: '0 0 10px', fontSize: '0.9rem', lineHeight: 1.65, color: '#4A4036' }}>
                  {para}
                </p>
              ) : (
                <ul key={j} style={{ margin: '0 0 10px', paddingLeft: 18 }}>
                  {para.map((li, k) => (
                    <li key={k} style={{ fontSize: '0.9rem', lineHeight: 1.6, color: '#4A4036', marginBottom: 5 }}>
                      {li}
                    </li>
                  ))}
                </ul>
              )
            )}
          </section>
        ))}

        <div style={{ borderTop: '1px solid #EADFD3', paddingTop: 16, marginTop: 8 }}>
          <p style={{ margin: 0, fontSize: '0.82rem', lineHeight: 1.6, color: '#888' }}>
            Questions or data requests? Email{' '}
            <a href="mailto:privacy@themshin.com" style={{ color: ACCENT, fontWeight: 700 }}>
              privacy@themshin.com
            </a>.
          </p>
        </div>
      </div>
    </div>
  )
}

type Section = { h: string; body: (string | string[])[] }

const PRIVACY_SECTIONS: Section[] = [
  {
    h: 'What we collect',
    body: [
      'When you use Cravings, we collect the following:',
      [
        'Account details — your name and email address when you register.',
        'Taste preferences — diet and allergen flags, and taste sliders you set during onboarding.',
        'Swipe behavior — which dishes you accept, reject, or block, including timestamps, used to build your recommendation model.',
        'Approximate location — only when you allow it, to find nearby restaurants. We do not store precise GPS coordinates.',
        'Device & session data — an authentication token stored in your browser so you stay signed in.',
      ],
    ],
  },
  {
    h: 'How we use it',
    body: [
      'Your data powers the core product: learning what you want to eat and surfacing restaurants nearby. We use swipe history to train your personal taste model, and preferences to filter recommendations. We do not sell your personal data.',
    ],
  },
  {
    h: 'How it is stored & how long',
    body: [
      'Account and swipe data are stored on our servers in encrypted form. Authentication tokens live in your browser\'s local storage until you log out. We retain your data for as long as your account is active. If you delete your account, your profile and swipe history are erased within 30 days.',
    ],
  },
  {
    h: 'Location data',
    body: [
      'Cravings requests your approximate location only to find nearby restaurants, and only after you grant permission. Location is used at request time and is not retained as a location history. You can revoke access at any time in your browser or device settings.',
    ],
  },
  {
    h: 'Your rights',
    body: [
      'Depending on where you live (including the EU under GDPR and California under CCPA), you have the right to:',
      [
        'Access — request a copy of the data we hold about you.',
        'Portability — export your data in a machine-readable format (JSON).',
        'Erasure — delete your account and all associated swipe history.',
        'Correction — update inaccurate account details.',
      ],
      'You can export or delete your data directly from your Profile, or by emailing us.',
    ],
  },
  {
    h: 'Cookies & local storage',
    body: [
      'We use essential local storage to keep you signed in and remember your taste model. With your consent, we may use optional analytics storage to improve recommendations. You control this from the consent banner shown on your first visit.',
    ],
  },
]

const TERMS_SECTIONS: Section[] = [
  {
    h: 'Acceptance',
    body: [
      'By using Cravings, you agree to these Terms of Service. If you do not agree, please do not use the app.',
    ],
  },
  {
    h: 'The service',
    body: [
      'Cravings is a food-discovery tool that suggests dishes and nearby restaurants based on your preferences and swipe behavior. Recommendations are for informational and entertainment purposes only.',
    ],
  },
  {
    h: 'Allergen & dietary disclaimer',
    body: [
      'Dietary and allergen tags shown in Cravings are best-effort and are NOT certified safe. Cravings does not prepare food and cannot verify ingredients, preparation methods, or cross-contamination. Nothing in the app is medical or dietary advice.',
      'You are solely responsible for confirming ingredients, allergens, and suitability directly with the restaurant before ordering or eating. If you have a food allergy or medical condition, consult the restaurant and a qualified professional.',
    ],
  },
  {
    h: 'Limitation of liability',
    body: [
      'To the maximum extent permitted by law, Cravings and its operators are not liable for any indirect, incidental, or consequential damages, or for any allergic reaction, illness, injury, or loss arising from food you choose to order or eat based on a recommendation. The service is provided "as is," without warranties of any kind. Our total liability for any claim is limited to the amount you paid us in the prior twelve months (which, for free accounts, is zero).',
    ],
  },
  {
    h: 'Indemnification',
    body: [
      'You agree to indemnify and hold harmless Cravings and its operators from any claims, damages, or expenses arising out of your use of the app, your reliance on any recommendation, or your violation of these Terms.',
    ],
  },
  {
    h: 'Accounts',
    body: [
      'You are responsible for keeping your login credentials secure and for activity under your account. You may delete your account at any time from your Profile.',
    ],
  },
  {
    h: 'Changes',
    body: [
      'We may update these Terms from time to time. Continued use of Cravings after changes take effect constitutes acceptance of the revised Terms.',
    ],
  },
]
