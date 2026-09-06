import { expect, test } from '@playwright/test';

test('completes a fully covered monitor request without creating a PR', async ({
  page,
}, testInfo) => {
  const failedApiResponses: string[] = [];
  const backendPort = process.env.E2E_BACKEND_PORT ?? '8010';
  const apiBaseUrl = `http://127.0.0.1:${backendPort}/api`;

  page.on('response', (response) => {
    if (
      response.url().startsWith(apiBaseUrl) &&
      response.status() >= 400
    ) {
      failedApiResponses.push(
        `${response.status()} ${response.request().method()} ${response.url()}`
      );
    }
  });

  await page.goto('/');
  await page.getByRole('button', { name: 'New Thread' }).click();
  await expect(page.getByText('Pending', { exact: true })).toHaveCount(4);
  await expect(page.getByText('In Progress', { exact: true })).toHaveCount(0);
  await page
    .getByPlaceholder(/Describe what you want to purchase/i)
    .fill('Need 5 4K monitors for UI/UX designers before Sept 15');
  await page.getByTitle('Send Message').click();

  const confirmButton = page.getByRole('button', {
    name: /Confirm Specifications & Proceed to Demand Analysis/i,
  });
  await expect(confirmButton).toBeVisible();
  await confirmButton.click();

  const recommendationCard = page.locator(
    'section[aria-labelledby="recommendation-title"]'
  );
  await expect(recommendationCard).toBeVisible();
  await expect(page.getByText('Awaiting Human Review', { exact: true })).toBeVisible();
  await expect(page.getByText('GeneratePR Agent', { exact: true })).toHaveCount(0);
  await expect(
    recommendationCard.getByText('Recommended net new purchase', {
      exact: true,
    })
  ).toBeVisible();
  await expect(recommendationCard.getByText('0', { exact: true })).toBeVisible();
  await expect(
    recommendationCard.getByText('units', { exact: true })
  ).toBeVisible();

  await recommendationCard
    .getByRole('button', { name: 'Accept 0 units' })
    .click();

  const completeButton = page.getByRole('button', {
    name: 'Complete Without Purchase',
    exact: true,
  });
  await expect(completeButton).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Submit PR', exact: true })
  ).toHaveCount(0);
  await completeButton.click();

  const dialog = page.getByRole('dialog', {
    name: 'Complete without creating a PR?',
  });
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText(
    'The reviewed final purchase quantity is 0 units'
  );
  await expect(dialog).toContainText(
    'No Purchase Requisition will be created or sent to ERP'
  );

  const resolutionResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith('/resolve-without-purchase') &&
      response.request().method() === 'POST'
  );
  await dialog
    .getByRole('button', { name: 'Complete Without Purchase' })
    .click();

  const response = await resolutionResponse;
  expect(response.ok()).toBe(true);
  const responseBody = await response.json();
  expect(responseBody.request_outcome).toBe('resolved_without_purchase');
  expect(responseBody).not.toHaveProperty('pr_number');
  expect(responseBody.pr?.pr_number).toBeFalsy();

  await expect(
    page.getByText('Request completed without a new purchase')
  ).toBeVisible();
  await expect(page.getByText('No PR Needed')).toBeVisible();
  await expect(page.getByText('Workflow Complete', { exact: true })).toBeVisible();
  await expect(page.getByText('PR Number')).toHaveCount(0);
  expect(failedApiResponses).toEqual([]);

  const chatScrollArea = page.getByTestId('chat-scroll-area');
  await expect
    .poll(() =>
      chatScrollArea.evaluate((element) => ({
        hasOverflow: element.scrollHeight > element.clientHeight,
        distanceFromBottom:
          element.scrollHeight - element.clientHeight - element.scrollTop,
      }))
    )
    .toEqual({ hasOverflow: true, distanceFromBottom: 0 });

  await page.screenshot({
    path: testInfo.outputPath('resolved-without-purchase.png'),
    fullPage: true,
  });
});
