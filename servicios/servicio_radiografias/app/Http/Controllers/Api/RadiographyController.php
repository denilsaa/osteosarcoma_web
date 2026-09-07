<?php

namespace App\Http\Controllers\Api;

use App\Application\Radiography\ListCaseRadiographicStudies;
use App\Http\Controllers\Controller;
use App\Http\Presenters\RadiographicStudyPresenter;
use Illuminate\Http\JsonResponse;
use InvalidArgumentException;
use Throwable;

final class RadiographyController extends Controller
{
    public function __construct(
        private readonly ListCaseRadiographicStudies $listCaseStudies,
    ) {
    }

    public function byCase(
        string $caseUuid
    ): JsonResponse {
        try {
            $studies = $this
                ->listCaseStudies
                ->execute(
                    $caseUuid
                );

            return response()->json(
                RadiographicStudyPresenter::collection(
                    $studies
                )
            );
        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' => 'INVALID_CASE_UUID',
                        'message' => $exception->getMessage(),
                    ],
                ],
                422
            );
        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' => 'RADIOGRAPHY_QUERY_ERROR',
                        'message' =>
                            'No fue posible consultar los estudios radiográficos.',
                    ],
                ],
                500
            );
        }
    }
}