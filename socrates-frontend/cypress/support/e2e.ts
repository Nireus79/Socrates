// Cypress support file for E2E tests
// https://docs.cypress.io/guides/tooling/plugins-guide.html

// Avoid TypeScript errors when accessing cy
declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>;
    }
  }
}

// Custom command to login
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.visit('/login');
  cy.get('input[name="username"]').type(username);
  cy.get('input[name="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/dashboard');
});

export {};
