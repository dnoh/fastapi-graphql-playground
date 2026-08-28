'use client';

/** Shared loading / error primitives so features don't re-invent them. */

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center text-gray-500">{label}</div>
  );
}

export function ErrorBanner({ message, code }: { message: string; code?: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
      <p className="font-medium">{message}</p>
      {code && <p className="mt-1 font-mono text-xs text-red-600">{code}</p>}
    </div>
  );
}

/** Pull the stable `extensions.code` off an Apollo error, if the API sent one. */
export function errorCode(error: unknown): string | undefined {
  const graphQLErrors = (error as { graphQLErrors?: { extensions?: { code?: unknown } }[] })
    ?.graphQLErrors;
  const code = graphQLErrors?.[0]?.extensions?.code;
  return typeof code === 'string' ? code : undefined;
}
