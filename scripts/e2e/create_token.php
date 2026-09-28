<?php

// Run inside the throwaway Firefly III container after system:create-first-user.
require '/var/www/html/vendor/autoload.php';
require '/var/www/html/bootstrap/app.php';

$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$user = FireflyIII\User::where('email', 'e2e@example.invalid')->firstOrFail();

// Firefly III normally creates this client when the user visits the OAuth page.
$repository = $app->make(Laravel\Passport\ClientRepository::class);
$repository->createPersonalAccessGrantClient('E2E personal access client', null);

echo $user->createToken('e2e-tests')->accessToken;
