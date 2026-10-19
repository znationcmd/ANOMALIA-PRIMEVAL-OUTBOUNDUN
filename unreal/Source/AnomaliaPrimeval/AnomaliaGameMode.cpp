#include "AnomaliaGameMode.h"
#include "AnomaliaSurvivor.h"

AAnomaliaGameMode::AAnomaliaGameMode()
{
    DefaultPawnClass = AAnomaliaSurvivor::StaticClass();
}
