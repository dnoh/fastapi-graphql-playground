import { gql } from "@apollo/client";

export const GET_LATEST_MESSAGES = gql`
  query GetLatestMessages($limit: Int) {
    latestMessages(limit: $limit) {
      id
      content
      createdAt
    }
  }
`;

export const CREATE_MESSAGE = gql`
  mutation CreateMessage($input: CreateMessageInput!) {
    createMessage(input: $input) {
      id
      content
      createdAt
    }
  }
`;
