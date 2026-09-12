<?php

namespace App\Providers;

use App\Domain\Radiography\Repositories\RadiographicFileRepository;
use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use App\Infrastructure\Persistence\Eloquent\Repositories\EloquentRadiographicFileRepository;
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


        $this->app->bind(
            RadiographicFileRepository::class,
            EloquentRadiographicFileRepository::class
        );
    }


    public function boot(): void
    {
        //
    }
}