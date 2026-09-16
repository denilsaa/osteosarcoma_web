<?php

namespace App\Domain\Radiography\Validation;

final readonly class RadiographicFileValidationReport
{
    /**
     * @param RadiographicValidationResult[] $results
     */
    public function __construct(
        public array $results,
    ) {
    }


    public function isValid(): bool
    {
        foreach (
            $this->results
            as
            $result
        ) {
            if (! $result->valid) {
                return false;
            }
        }

        return true;
    }


    public function status(): string
    {
        return $this->isValid()
            ? 'VALIDA'
            : 'RECHAZADA';
    }


    /**
     * @return RadiographicValidationResult[]
     */
    public function failures(): array
    {
        return array_values(
            array_filter(
                $this->results,
                static fn (
                    RadiographicValidationResult $result
                ): bool =>
                    ! $result->valid
            )
        );
    }


    public function firstReason(): ?string
    {
        foreach (
            $this->failures()
            as
            $failure
        ) {
            if (
                $failure->reason !== null
                &&
                trim(
                    $failure->reason
                ) !== ''
            ) {
                return $failure->reason;
            }
        }

        return null;
    }


    public function firstCorrection(): ?string
    {
        foreach (
            $this->failures()
            as
            $failure
        ) {
            if (
                $failure->correction !== null
                &&
                trim(
                    $failure->correction
                ) !== ''
            ) {
                return $failure->correction;
            }
        }

        return null;
    }
}