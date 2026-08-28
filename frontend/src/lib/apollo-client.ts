import { ApolloClient, InMemoryCache } from "@apollo/client";

import { env } from "~/env";

export const client = new ApolloClient({
  // Full GraphQL endpoint; override with NEXT_PUBLIC_API_URL (see .env.example).
  uri: env.NEXT_PUBLIC_API_URL,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: "no-cache",
      errorPolicy: "all",
    },
    query: {
      fetchPolicy: "no-cache",
      errorPolicy: "all",
    },
  },
});
