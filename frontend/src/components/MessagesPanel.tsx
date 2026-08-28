'use client';

import { useState } from 'react';

import {
  useCreateMessageMutation,
  useGetLatestMessagesQuery,
} from '~/generated/graphql';

import { ErrorBanner, Loading, errorCode } from './ui/Feedback';

export default function MessagesPanel() {
  const [content, setContent] = useState('');

  const { data, loading, error, refetch } = useGetLatestMessagesQuery({
    variables: { limit: 10 },
  });

  const [createMessage, { loading: creating, error: createError }] =
    useCreateMessageMutation();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) return;

    await createMessage({ variables: { input: { content: trimmed } } });
    setContent('');
    await refetch();
  }

  const messages = data?.latestMessages ?? [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <header>
          <h1 className="text-3xl font-bold text-gray-900">Brex Interview Playground</h1>
          <p className="text-gray-600">Messages — the vertical slice template.</p>
        </header>

        <form onSubmit={handleSubmit} className="rounded-lg bg-white p-6 shadow">
          <label htmlFor="content" className="mb-2 block font-medium text-gray-900">
            New message
          </label>
          <div className="flex gap-2">
            <input
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Say something…"
              className="flex-1 rounded-md border border-gray-300 px-3 py-2"
            />
            <button
              type="submit"
              disabled={creating || !content.trim()}
              className="rounded-md bg-gray-900 px-4 py-2 font-medium text-white disabled:opacity-40"
            >
              {creating ? 'Adding…' : 'Add'}
            </button>
          </div>
          {createError && (
            <div className="mt-4">
              <ErrorBanner message={createError.message} code={errorCode(createError)} />
            </div>
          )}
        </form>

        <section className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Recent messages</h2>

          {loading ? (
            <Loading />
          ) : error ? (
            <ErrorBanner message={error.message} code={errorCode(error)} />
          ) : messages.length === 0 ? (
            <p className="py-8 text-center text-gray-500">No messages yet</p>
          ) : (
            <ul className="space-y-3">
              {messages.map((message) => (
                <li
                  key={message.id}
                  className="rounded-lg border border-gray-200 p-4"
                >
                  <p className="font-medium text-gray-900">{message.content}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(message.createdAt).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
