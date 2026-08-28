import type { CodegenConfig } from '@graphql-codegen/cli'

const config: CodegenConfig = {
  // Local SDL exported by `make schema` — codegen needs no running server,
  // and the schema file is committed so API changes show up in the diff.
  schema: './schema.graphql',
  documents: ['src/**/*.tsx', 'src/**/*.ts'], // Files containing your GraphQL operations
  generates: {
    './src/generated/graphql.ts': {
      plugins: [
        'typescript',
        'typescript-operations',
        'typescript-react-apollo'
      ],
      config: {
        withHooks: true,
        withComponent: false,
        withHOC: false,
        // Strawberry emits DateTime/UUID scalars. Without this map codegen
        // silently types them as `any`; strictScalars makes any NEW unmapped
        // scalar a loud build error instead of a silent `any`.
        scalars: { DateTime: 'string', UUID: 'string' },
        strictScalars: true,
      },
    },
  },
}

export default config 