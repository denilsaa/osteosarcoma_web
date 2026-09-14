<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('tipos_estudio', function (Blueprint $table) {
            $table
                ->boolean('activo')
                ->default(true);
        });

        Schema::table('regiones_anatomicas', function (Blueprint $table) {
            $table
                ->boolean('activo')
                ->default(true);
        });
    }

    public function down(): void
    {
        Schema::table('tipos_estudio', function (Blueprint $table) {
            $table->dropColumn('activo');
        });

        Schema::table('regiones_anatomicas', function (Blueprint $table) {
            $table->dropColumn('activo');
        });
    }
};