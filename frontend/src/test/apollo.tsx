import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  InMemoryCache,
  Observable,
  type FetchResult,
  type Operation,
} from "@apollo/client";
import { GraphQLError } from "graphql";

/** Every operation the component sent, in order. */
export type Sent = { name: string; variables: Record<string, unknown> };

type Reply = FetchResult | Error;
type Respond = (
  operation: Operation,
  callIndex: number,
) => Reply | Promise<Reply>;

/**
 * An Apollo client wired to a stub link.
 *
 * A stub link rather than MockedProvider because these tests assert on the
 * *variables* a component sends — specifically which idempotency key it reuses
 * — and matching a randomly generated key against a fixed mock is not possible.
 */
export function stubClient(respond: Respond) {
  const sent: Sent[] = [];
  let calls = 0;

  const link = new ApolloLink(
    (operation) =>
      new Observable<FetchResult>((observer) => {
        sent.push({
          name: operation.operationName,
          variables: operation.variables as Record<string, unknown>,
        });
        void Promise.resolve(respond(operation, calls++)).then((reply) => {
          if (reply instanceof Error) {
            observer.error(reply);
            return;
          }
          observer.next(reply);
          observer.complete();
        });
      }),
  );

  const client = new ApolloClient({
    link,
    cache: new InMemoryCache(),
    defaultOptions: {
      watchQuery: { fetchPolicy: "no-cache" },
      query: { fetchPolicy: "no-cache" },
    },
  });

  function Provider({ children }: { children: React.ReactNode }) {
    return <ApolloProvider client={client}>{children}</ApolloProvider>;
  }

  return { Provider, sent };
}

/** A GraphQL-level refusal, the shape the server sends with a stable code. */
export function domainError(code: string, message = "refused"): FetchResult {
  return {
    data: null,
    errors: [new GraphQLError(message, { extensions: { code } })],
  };
}
