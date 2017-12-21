import numpy as np
from SimPEG import (Maps, Utils, DataMisfit, Regularization,
                    Optimization, Inversion, InvProblem, Directives)


def run_inversion(
    m0, survey, actind, mesh,
    std, eps,
    maxIter=15, beta0_ratio=1e0,
    coolingFactor=5, coolingRate=2,
    upper=np.inf, lower=-np.inf,
    use_sensitivity_weight=True
):
    """
    Run IP inversion
    """
    dmisfit = DataMisfit.l2_DataMisfit(survey)
    uncert = abs(survey.dobs) * std + eps
    dmisfit.W = 1./uncert
    # Map for a regularization
    regmap = Maps.IdentityMap(nP=int(actind.sum()))
    # Related to inversion
    if use_sensitivity_weight:
        reg = Regularization.Simple(mesh, indActive=actind, mapping=regmap)
    else:
        reg = Regularization.Tikhonov(mesh, indActive=actind, mapping=regmap)
    opt = Optimization.ProjectedGNCG(maxIter=maxIter, upper=upper, lower=lower)
    invProb = InvProblem.BaseInvProblem(dmisfit, reg, opt)
    beta = Directives.BetaSchedule(
        coolingFactor=coolingFactor, coolingRate=coolingRate
    )
    betaest = Directives.BetaEstimate_ByEig(beta0_ratio=beta0_ratio)
    target = Directives.TargetMisfit()

    # Need to have basice saving function
    if use_sensitivity_weight:
        updateSensW = Directives.UpdateSensitivityWeights()
        update_Jacobi = Directives.UpdatePreconditioner()
        directiveList = [
            beta, betaest, target, updateSensW, update_Jacobi
        ]
    else:
        directiveList = [
            beta, betaest, target
        ]
    inv = Inversion.BaseInversion(
        invProb, directiveList=directiveList
        )
    opt.LSshorten = 0.5
    opt.remember('xc')

    # Run inversion
    mopt = inv.run(m0)
    return mopt, invProb.dpred
