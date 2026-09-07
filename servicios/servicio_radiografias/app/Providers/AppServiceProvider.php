<?php

namespace App\Providers;

use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use App\Infrastructure\Persistence\Eloquent\Repositories\EloquentRadiographicStudyRepository;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(
            RadiographicStudyRepository::class,
            EloquentRadiographicStudyRepository::class
        );
    }

    public function boot(): void
    {
        //
    }
}