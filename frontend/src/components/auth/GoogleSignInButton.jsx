import { useGoogleLogin } from '@react-oauth/google';

export default function GoogleSignInButton(props) {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  if (!clientId) return null;
  return <GoogleSignInButtonInner {...props} />;
}

function GoogleSignInButtonInner({ onSuccess, onError, loading }) {
  const login = useGoogleLogin({
    onSuccess: (tokenResponse) => onSuccess(tokenResponse.access_token),
    onError: () => onError?.('Google sign-in was cancelled or failed'),
    scope: 'openid email profile',
  });

  return (
    <button
      type="button"
      disabled={loading}
      onClick={() => login()}
      className="inline-flex w-full items-center justify-center gap-2.5 rounded-xl border border-white/15 bg-white/[0.04] py-3 text-sm font-semibold text-white/90 transition-colors hover:bg-white/[0.08] disabled:opacity-70"
    >
      {loading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
      ) : (
        <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="#EA4335"
            d="M12 10.2v3.6h5.1c-.2 1.2-1.5 3.6-5.1 3.6-3.1 0-5.6-2.5-5.6-5.6S8.9 6.2 12 6.2c1.7 0 2.9.7 3.6 1.3l2.4-2.4C16.4 3.6 14.4 2.7 12 2.7 6.9 2.7 2.7 6.9 2.7 12S6.9 21.3 12 21.3c5.5 0 9.1-3.8 9.1-9.2 0-.6-.1-1.1-.2-1.6H12z"
          />
          <path fill="#4285F4" d="M21.1 12.1c0-.6-.1-1.1-.2-1.6H12v3.6h5.1c-.3 1.4-1.4 2.5-2.9 3.1l3.3 2.5c1.9-1.8 3.6-4.6 3.6-7.6z" />
          <path fill="#FBBC05" d="M6.4 14.3A5.6 5.6 0 0 1 6.1 12c0-.8.1-1.6.3-2.3L3.1 7.1A9.26 9.26 0 0 0 2.7 12c0 1.5.4 2.9 1.1 4.1l2.6-1.8z" />
          <path fill="#34A853" d="M12 21.3c2.4 0 4.4-.8 5.9-2.1l-3.3-2.5c-.9.6-2.1 1-3.4 1-2.6 0-4.8-1.7-5.6-4.1L3.1 16.1C4.4 18.9 8 21.3 12 21.3z" />
        </svg>
      )}
      Continue with Google
    </button>
  );
}
